import { IAutocompletionRegistry } from '@jupyter/chat';
import { IGlobalAwareness } from '@jupyter/collaboration';
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
  ILayoutRestorer
} from '@jupyterlab/application';
import {
  IWidgetTracker,
  ReactWidget,
  IThemeManager,
  MainAreaWidget,
  ICommandPalette
} from '@jupyterlab/apputils';
import { IDocumentWidget } from '@jupyterlab/docregistry';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { Signal } from '@lumino/signaling';
import type { Awareness } from 'y-protocols/awareness';

import { ChatHandler } from './chat_handler';
import { completionPlugin } from './completions';
import { ActiveCellManager } from './contexts/active-cell-context';
import { SelectionWatcher } from './selection-watcher';
import { menuPlugin } from './plugins/menu-plugin';
import { autocompletion } from './slash-autocompletion';
import { statusItemPlugin } from './status';
import {
  IJaiCompletionProvider,
  IJaiCore,
  IJaiMessageFooter,
  IJaiTelemetryHandler
} from './tokens';
import { buildErrorWidget } from './widgets/chat-error';
import { buildChatSidebar } from './widgets/chat-sidebar';
import { buildAiSettings } from './widgets/settings-widget';

export type DocumentTracker = IWidgetTracker<IDocumentWidget>;

export namespace CommandIDs {
  /**
   * Command to focus the input.
   */
  export const focusChatInput = 'jupyter-ai:focus-chat-input';
  /**
   * Command to open the AI settings.
   */
  export const openAiSettings = 'jupyter-ai:open-settings';
}

/**
 * Initialization data for the jupyter_ai extension.
 */
const plugin: JupyterFrontEndPlugin<IJaiCore> = {
  id: '@jupyter-ai/core:plugin',
  autoStart: true,
  requires: [IRenderMimeRegistry],
  optional: [
    ICommandPalette,
    IGlobalAwareness,
    ILayoutRestorer,
    IThemeManager,
    IJaiCompletionProvider,
    IJaiMessageFooter,
    IJaiTelemetryHandler
  ],
  provides: IJaiCore,
  activate: async (
    app: JupyterFrontEnd,
    rmRegistry: IRenderMimeRegistry,
    palette: ICommandPalette | null,
    globalAwareness: Awareness | null,
    restorer: ILayoutRestorer | null,
    themeManager: IThemeManager | null,
    completionProvider: IJaiCompletionProvider | null,
    messageFooter: IJaiMessageFooter | null,
    telemetryHandler: IJaiTelemetryHandler | null
  ) => {
    /**
     * Initialize selection watcher singleton
     */
    const selectionWatcher = new SelectionWatcher(app.shell);

    /**
     * Initialize active cell manager singleton
     */
    const activeCellManager = new ActiveCellManager(app.shell);

    /**
     * Initialize chat handler, open WS connection
     */
    const chatHandler = new ChatHandler();

    const openInlineCompleterSettings = () => {
      app.commands.execute('settingeditor:open', {
        query: 'Inline Completer'
      });
    };

    const focusInputSignal = new Signal<unknown, void>({});

    // Create a AI settings widget.
    let aiSettings: MainAreaWidget<ReactWidget>;
    let settingsWidget: ReactWidget;
    try {
      await chatHandler.initialize();
      settingsWidget = buildAiSettings(
        rmRegistry,
        completionProvider,
        openInlineCompleterSettings
      );
    } catch (e) {
      settingsWidget = buildErrorWidget(themeManager);
    }

    // Add a command to open settings widget in main area.
    app.commands.addCommand(CommandIDs.openAiSettings, {
      execute: () => {
        if (!aiSettings || aiSettings.isDisposed) {
          aiSettings = new MainAreaWidget({ content: settingsWidget });
          aiSettings.id = 'jupyter-ai-settings';
          aiSettings.title.label = 'AI settings';
          aiSettings.title.closable = true;
        }
        if (!aiSettings.isAttached) {
          app?.shell.add(aiSettings, 'main');
        }
        app.shell.activateById(aiSettings.id);
      },
      label: 'AI settings'
    });

    if (palette) {
      palette.addItem({
        category: 'jupyter-ai',
        command: CommandIDs.openAiSettings
      });
    }

    let chatWidget: ReactWidget;
    try {
      chatWidget = buildChatSidebar(
        selectionWatcher,
        chatHandler,
        globalAwareness,
        themeManager,
        rmRegistry,
        completionProvider,
        openInlineCompleterSettings,
        activeCellManager,
        focusInputSignal,
        messageFooter,
        telemetryHandler,
        app.serviceManager.user
      );
    } catch (e) {
      chatWidget = buildErrorWidget(themeManager);
    }

    /**
     * Add Chat widget to right sidebar
     */
    app.shell.add(chatWidget, 'left', { rank: 2000 });

    if (restorer) {
      restorer.add(chatWidget, 'jupyter-ai-chat');
    }

    // Define jupyter-ai commands
    app.commands.addCommand(CommandIDs.focusChatInput, {
      execute: () => {
        app.shell.activateById(chatWidget.id);
        focusInputSignal.emit();
      },
      label: 'Focus the jupyter-ai chat'
    });

    return {
      activeCellManager,
      chatHandler,
      chatWidget,
      selectionWatcher
    };
  }
};

/**
 * Add slash commands to collaborative chat.
 */
const collaborative_autocompletion: JupyterFrontEndPlugin<void> = {
  id: '@jupyter-ai/core:autocompletion',
  autoStart: true,
  requires: [IAutocompletionRegistry],
  activate: async (
    app: JupyterFrontEnd,
    autocompletionRegistry: IAutocompletionRegistry
  ) => {
    autocompletionRegistry.add('ai', autocompletion);
  }
};

export default [
  plugin,
  statusItemPlugin,
  completionPlugin,
  menuPlugin,
  collaborative_autocompletion
];

export * from './contexts';
export * from './tokens';
