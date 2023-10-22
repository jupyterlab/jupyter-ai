import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
  ILayoutRestorer
} from '@jupyterlab/application';

import { IWidgetTracker, ReactWidget } from '@jupyterlab/apputils';
import { IDocumentWidget } from '@jupyterlab/docregistry';
import { IGlobalAwareness } from '@jupyter/collaboration';
import type { Awareness } from 'y-protocols/awareness';
import { buildChatSidebar } from './widgets/chat-sidebar';
import { buildBigcodeSidebar } from './widgets/bigcode-sidebar';
import { SelectionWatcher } from './selection-watcher';
import { ChatHandler } from './chat_handler';
import { buildErrorWidget } from './widgets/chat-error';
import { handleCodeCompletionKeyDown } from './inline-completion-handler';
import { ICompletionProviderManager } from '@jupyterlab/completer';
import { ITranslator, nullTranslator } from '@jupyterlab/translation';
import { BigcodeInlineCompletionProvider } from './bigcode-Inline-completion-provider';

export type DocumentTracker = IWidgetTracker<IDocumentWidget>;

/**
 * Initialization data for the jupyter_ai extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyter_ai:plugin',
  autoStart: true,
  optional: [IGlobalAwareness, ILayoutRestorer],
  activate: async (
    app: JupyterFrontEnd,
    globalAwareness: Awareness | null,
    restorer: ILayoutRestorer | null
  ) => {
    /**
     * Initialize selection watcher singleton
     */
    const selectionWatcher = new SelectionWatcher(app.shell);

    /**
     * Initialize chat handler, open WS connection
     */
    const chatHandler = new ChatHandler();

    let chatWidget: ReactWidget | null = null;
    try {
      await chatHandler.initialize();
      chatWidget = buildChatSidebar(
        selectionWatcher,
        chatHandler,
        globalAwareness
      );
    } catch (e) {
      chatWidget = buildErrorWidget();
    }

    /**
     * Add Chat widget to right sidebar
     */
    app.shell.add(chatWidget, 'left', { rank: 2000 });

    if (restorer) {
      restorer.add(chatWidget, 'jupyter-ai-chat');
    }
  }
};

const bigcodeCodeCompletion: JupyterFrontEndPlugin<void> = {
  id: 'jupyter_ai:plugin:inline-bigcode',
  description: 'Adds inline completion provider suggesting code from bigcode.',
  requires: [ICompletionProviderManager],
  optional: [ILayoutRestorer],
  autoStart: true,
  activate: (
    app: JupyterFrontEnd,
    completionManager: ICompletionProviderManager,
    restorer: ILayoutRestorer | null,
    translator: ITranslator | null
  ): void => {
    /**
     * Initialize bigcode settings widget
     */
    const bigcodeWidget = buildBigcodeSidebar();

    /**
     * Add Bigcode settings widget to right sidebar
     */
    app.shell.add(bigcodeWidget, 'left', { rank: 2001 });

    if (restorer) {
      restorer.add(bigcodeWidget, 'bigcode-code-completion');
    }

    const bigcodeInlineCompletionProvider = new BigcodeInlineCompletionProvider(
      {
        translator: translator ?? nullTranslator
      }
    );

    completionManager.registerInlineProvider(bigcodeInlineCompletionProvider);

    /**
     * Initialize keydown handler
     */
    handleCodeCompletionKeyDown(
      app,
      completionManager,
      bigcodeInlineCompletionProvider
    );
  }
};

const plugins: JupyterFrontEndPlugin<void>[] = [plugin, bigcodeCodeCompletion];

export default plugins;
