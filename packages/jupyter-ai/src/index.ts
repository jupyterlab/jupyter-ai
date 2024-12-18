import { IAutocompletionRegistry } from '@jupyter/chat';
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
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

import { ChatHandler } from './chat_handler';
import { completionPlugin } from './completions';
import { autocompletion } from './slash-autocompletion';
import { statusItemPlugin } from './status';
import { IJaiCompletionProvider, IJaiCore } from './tokens';
import { buildErrorWidget } from './widgets/chat-error';
import { buildAiSettings } from './widgets/settings-widget';

export type DocumentTracker = IWidgetTracker<IDocumentWidget>;

export namespace CommandIDs {
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
  optional: [ICommandPalette, IThemeManager, IJaiCompletionProvider],
  provides: IJaiCore,
  activate: async (
    app: JupyterFrontEnd,
    rmRegistry: IRenderMimeRegistry,
    palette: ICommandPalette | null,
    themeManager: IThemeManager | null,
    completionProvider: IJaiCompletionProvider | null
  ) => {
    /**
     * Initialize chat handler, open WS connection
     */
    const chatHandler = new ChatHandler();

    const openInlineCompleterSettings = () => {
      app.commands.execute('settingeditor:open', {
        query: 'Inline Completer'
      });
    };

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

    return {
      chatHandler
    };
  }
};

/**
 * Add slash commands to jupyterlab chat.
 */
const chat_autocompletion: JupyterFrontEndPlugin<void> = {
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
  chat_autocompletion
];

export * from './contexts';
export * from './tokens';
