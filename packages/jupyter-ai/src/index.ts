import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
  ILayoutRestorer
} from '@jupyterlab/application';
import { INotebookTracker } from '@jupyterlab/notebook';
import { IEditorTracker } from '@jupyterlab/fileeditor';
import { IWidgetTracker } from '@jupyterlab/apputils';
import { IDocumentWidget } from '@jupyterlab/docregistry';
import { IGlobalAwareness } from '@jupyterlab/collaboration';
import type { Awareness } from 'y-protocols/awareness';

import {
  buildNotebookShortcutCommand,
  buildDefaultInserter,
  buildNotebookInserter,
  buildOpenTaskDialog
} from './commands';
import { psychologyIcon } from './icons';
import { getTextSelection } from './utils';
import { buildChatSidebar } from './widgets/chat-sidebar';
import { SelectionWatcher } from './selection-watcher';
import { ChatHandler } from './chat_handler';

export enum NotebookTasks {
  GenerateCode = 'generate-code-in-cells-below',
  ExplainCode = 'explain-code-in-cells-above'
}

export namespace CommandIDs {
  export const explainCodeCell = 'ai:explain-code-cell';
  export const codifyMdCell = 'ai:codify-md-cell';
  export const explainOrCodifyCell = 'ai:explain-or-codify-cell';
  export const generateFromNotebookSelection =
    'ai:generate-from-notebook-selection';
  export const generateFromEditorSelection =
    'ai:generate-from-editor-selection';
  export const insertAbove = 'ai:insert-above';
  export const insertBelow = 'ai:insert-below';
  export const insertReplace = 'ai:insert-replace';
  export const insertAboveInCells = 'ai:insert-above-in-cells';
  export const insertBelowInCells = 'ai:insert-below-in-cells';
}

export type DocumentTracker = IWidgetTracker<IDocumentWidget>;

/**
 * Initialization data for the jupyter_ai extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyter_ai:plugin',
  autoStart: true,
  requires: [INotebookTracker, IEditorTracker],
  optional: [IGlobalAwareness, ILayoutRestorer],
  activate: async (
    app: JupyterFrontEnd,
    notebookTracker: INotebookTracker,
    editorTracker: IEditorTracker,
    globalAwareness: Awareness | null,
    restorer: ILayoutRestorer
  ) => {
    const { commands, shell } = app;

    /**
     * Register core commands
     */
    commands.addCommand(CommandIDs.generateFromNotebookSelection, {
      execute: buildOpenTaskDialog(notebookTracker, app),
      label: 'Generate output from selection with AI...',
      icon: psychologyIcon,
      isEnabled: () => {
        const editorWidget = notebookTracker?.currentWidget?.content;
        return !!(editorWidget && getTextSelection(editorWidget));
      }
    });
    commands.addCommand(CommandIDs.generateFromEditorSelection, {
      execute: buildOpenTaskDialog(editorTracker, app),
      label: 'Generate output from selection with AI...',
      icon: psychologyIcon,
      isEnabled: () => {
        const editorWidget = editorTracker?.currentWidget?.content;
        return !!(editorWidget && getTextSelection(editorWidget));
      }
    });

    /**
     * Initialize selection watcher singleton
     */
    const selectionWatcher = new SelectionWatcher(shell);

    /**
     * Initialize chat handler, open WS connection
     */
    const chatHandler = new ChatHandler();
    await chatHandler.initialize();

    const chatWidget = buildChatSidebar(selectionWatcher, chatHandler, globalAwareness);

    /**
     * Add Chat widget to right sidebar
     */
    shell.add(
      chatWidget,
      'left', { rank: 2000 }
    );

    if (restorer) {
      restorer.add(chatWidget, 'jupyter-ai-chat');
    }

    /**
     * Register inserters
     */
    // default inserters
    commands.addCommand(CommandIDs.insertAbove, {
      execute: buildDefaultInserter('above') as any
    });
    commands.addCommand(CommandIDs.insertBelow, {
      execute: buildDefaultInserter('below') as any
    });
    commands.addCommand(CommandIDs.insertReplace, {
      execute: buildDefaultInserter('replace') as any
    });
    // gpt3 inserters
    commands.addCommand(CommandIDs.insertAboveInCells, {
      execute: buildNotebookInserter('above-in-cells') as any
    });
    commands.addCommand(CommandIDs.insertBelowInCells, {
      execute: buildNotebookInserter('below-in-cells') as any
    });

    /**
     * Register notebook shortcuts
     */
    commands.addCommand(CommandIDs.explainCodeCell, {
      execute: buildNotebookShortcutCommand(notebookTracker, app),
      label: 'Explain cell with AI',
      icon: psychologyIcon
    });
    commands.addCommand(CommandIDs.codifyMdCell, {
      execute: buildNotebookShortcutCommand(notebookTracker, app),
      label: 'Codify cell with AI',
      icon: psychologyIcon
    });
    commands.addCommand(CommandIDs.explainOrCodifyCell, {
      execute: buildNotebookShortcutCommand(notebookTracker, app),
      label: 'Explain or codify cell with AI',
      icon: psychologyIcon
    });
  }
};

export default plugin;
export type { InsertionContext } from './inserter';
