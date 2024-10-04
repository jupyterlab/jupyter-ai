import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
  ILayoutRestorer
} from '@jupyterlab/application';

import {
  IWidgetTracker,
  ReactWidget,
  IThemeManager
} from '@jupyterlab/apputils';
import { IDocumentWidget } from '@jupyterlab/docregistry';
import { IGlobalAwareness } from '@jupyter/collaboration';
import type { Awareness } from 'y-protocols/awareness';
import { buildChatSidebar } from './widgets/chat-sidebar';
import { SelectionWatcher } from './selection-watcher';
import { ChatHandler } from './chat_handler';
import { buildErrorWidget } from './widgets/chat-error';
import { completionPlugin } from './completions';
import { statusItemPlugin } from './status';
import { IJaiCompletionProvider, IJaiCore, IJaiMessageFooter } from './tokens';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { ActiveCellManager } from './contexts/active-cell-context';
import { Signal } from '@lumino/signaling';
import { menuPlugin } from './plugins/menu-plugin';

export type DocumentTracker = IWidgetTracker<IDocumentWidget>;

export namespace CommandIDs {
  /**
   * Command to focus the input.
   */
  export const focusChatInput = 'jupyter-ai:focus-chat-input';
}

/**
 * Initialization data for the jupyter_ai extension.
 */
const plugin: JupyterFrontEndPlugin<IJaiCore> = {
  id: '@jupyter-ai/core:plugin',
  autoStart: true,
  requires: [IRenderMimeRegistry],
  optional: [
    IGlobalAwareness,
    ILayoutRestorer,
    IThemeManager,
    IJaiCompletionProvider,
    IJaiMessageFooter
  ],
  provides: IJaiCore,
  activate: async (
    app: JupyterFrontEnd,
    rmRegistry: IRenderMimeRegistry,
    globalAwareness: Awareness | null,
    restorer: ILayoutRestorer | null,
    themeManager: IThemeManager | null,
    completionProvider: IJaiCompletionProvider | null,
    messageFooter: IJaiMessageFooter | null
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

    let chatWidget: ReactWidget;
    try {
      await chatHandler.initialize();
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
        messageFooter
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

export default [plugin, statusItemPlugin, completionPlugin, menuPlugin];

export * from './tokens';
