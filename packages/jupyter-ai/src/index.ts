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
import { SelectionWatcher } from './selection-watcher';
import { ChatHandler } from './chat_handler';
import { buildErrorWidget } from './widgets/chat-error';
import { AiService } from './handler';

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

    let chatWidget: ReactWidget | null = null;
    let chatHandler: ChatHandler | null = null;

    try {
      // Fetch configuration to check for critical errors
      const config = await AiService.getConfig();
      console.log('\n\n\n *** \n\n\n');
      console.log(config.config_errors);
      const hasCriticalErrors = config.config_errors?.some(
        error => error.error_type === AiService.ConfigErrorType.CRITICAL
      );

      if (!hasCriticalErrors) {
        /**
         * Initialize chat handler, open WS connection
         */
        chatHandler = new ChatHandler();
        await chatHandler.initialize();
      }
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

export default plugin;
