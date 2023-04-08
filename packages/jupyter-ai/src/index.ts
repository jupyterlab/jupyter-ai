import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { INotebookTracker } from '@jupyterlab/notebook';
import { IEditorTracker } from '@jupyterlab/fileeditor';
import { IWidgetTracker } from '@jupyterlab/apputils';
import { IDocumentWidget } from '@jupyterlab/docregistry';

import {
  buildNotebookShortcutCommand,
  buildDefaultInserter,
  buildNotebookInserter,
  buildOpenTaskDialog
} from './commands';
import { psychologyIcon } from './icons';
import { getTextSelection } from './utils';

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
  activate: (
    app: JupyterFrontEnd,
    notebookTracker: INotebookTracker,
    editorTracker: IEditorTracker
  ) => {
    const { commands } = app;

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
