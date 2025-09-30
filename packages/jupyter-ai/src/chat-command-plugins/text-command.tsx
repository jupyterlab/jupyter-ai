/*
 * Copyright (c) Jupyter Development Team.
 * Distributed under the terms of the Modified BSD License.
 */

import React from 'react';
import { JupyterFrontEndPlugin } from '@jupyterlab/application';
import { INotebookTracker } from '@jupyterlab/notebook';
import {
  IChatCommandProvider,
  IChatCommandRegistry,
  IInputModel,
  ChatCommand
} from '@jupyter/chat';
import TextFieldsIcon from '@mui/icons-material/TextFields';

const SELECTION_COMMAND_PROVIDER_ID =
  '@jupyter-ai/core:selection-command-provider';

/**
 * A command provider that provides completions for `@selection` commands and handles
 * `@selection` command calls.
 */
export class SelectionCommandProvider implements IChatCommandProvider {
  public id: string = SELECTION_COMMAND_PROVIDER_ID;

  constructor(
    private shell: any,
    private notebookTracker: INotebookTracker
  ) {}

  /**
   * Regex that matches all potential `@selection` commands.
   */
  _regex: RegExp = /@selection/g;

  async listCommandCompletions(
    inputModel: IInputModel
  ): Promise<ChatCommand[]> {
    // do nothing if the current word does not start with '@'.
    const currentWord = inputModel.currentWord;
    if (!currentWord || !currentWord.startsWith('@')) {
      return [];
    }

    // Check if any selection is available (prefer text selection, fallback to active cell)
    const hasTextSelection = !!inputModel.selectionWatcher?.selection;
    const hasActiveCell = inputModel.activeCellManager?.available;

    // Don't show @selection if no options are available
    if (!hasTextSelection && !hasActiveCell) {
      return [];
    }

    // if the current word matches the start of @selection, complete it
    if ('@selection'.startsWith(currentWord)) {
      const description = hasTextSelection
        ? 'Include selected text'
        : 'Include active cell content';

      return [
        {
          name: '@selection',
          providerId: this.id,
          description,
          icon: <TextFieldsIcon />,
          replaceWith: '@selection',
          spaceOnAccept: true
        }
      ];
    }

    // otherwise, return nothing as this provider cannot provide any completions
    // for the current word.
    return [];
  }

  async onSubmit(inputModel: IInputModel): Promise<void> {
    // Check if the input contains @selection
    if (!this._regex.test(inputModel.value)) {
      return;
    }

    // Get the current widget from the shell
    const currentWidget = this.shell.currentWidget;
    if (!currentWidget) {
      return;
    }

    // Get the document context to access the path
    const documentManager = inputModel.documentManager;
    if (!documentManager) {
      return;
    }

    const context = documentManager.contextForWidget(currentWidget as any);
    if (!context) {
      return;
    }

    const path = context.path;

    // Prefer text selection, fallback to active cell
    const selection = inputModel.selectionWatcher?.selection;
    const activeCellManager = inputModel.activeCellManager;

    if (selection && selection.text.trim().length > 0) {
      // Text selection with actual content - create attachment with selection range
      if (path.endsWith('.ipynb') && selection.cellId) {
        // Notebook with cell selection - get the cell type from the active cell
        const notebook = this.notebookTracker.currentWidget;
        if (!notebook) {
          return;
        }

        // Find the cell by ID to get its type
        const cell = notebook.content.widgets.find(
          c => c.model.id === selection.cellId
        );
        const cellType = cell?.model.type ?? 'code';
        const inputType =
          cellType === 'code'
            ? 'code'
            : cellType === 'markdown'
              ? 'markdown'
              : 'raw';

        inputModel.addAttachment?.({
          type: 'notebook',
          value: path,
          cells: [
            {
              id: selection.cellId,
              input_type: inputType,
              selection: {
                start: [selection.start.line, selection.start.column],
                end: [selection.end.line, selection.end.column],
                content: selection.text
              }
            }
          ]
        });
      } else {
        // Regular file with selection
        inputModel.addAttachment?.({
          type: 'file',
          value: path,
          selection: {
            start: [selection.start.line, selection.start.column],
            end: [selection.end.line, selection.end.column],
            content: selection.text
          }
        });
      }
    } else if (activeCellManager?.available && path.endsWith('.ipynb')) {
      // No meaningful text selection, but active cell is available in notebook
      const notebook = this.notebookTracker.currentWidget;
      if (!notebook) {
        return;
      }

      const activeCell = notebook.content.activeCell;
      if (!activeCell) {
        return;
      }

      // Get cell ID and type
      const cellId = activeCell.model.id;
      const cellType = activeCell.model.type;
      const inputType =
        cellType === 'code' ? 'code' : cellType === 'markdown' ? 'markdown' : 'raw';

      // Attach the specific cell without selection range
      inputModel.addAttachment?.({
        type: 'notebook',
        value: path,
        cells: [
          {
            id: cellId,
            input_type: inputType
          }
        ]
      });
    }

    // replace @selection command with a label for readability
    inputModel.value = inputModel.value.replace(this._regex, `\`selection\``);

    return;
  }
}

export const selectionCommandPlugin: JupyterFrontEndPlugin<void> = {
  id: '@jupyter-ai/core:selection-command-plugin',
  description: 'Adds support for the @selection command in Jupyter AI.',
  autoStart: true,
  requires: [IChatCommandRegistry],
  optional: [INotebookTracker],
  activate: (
    app,
    registry: IChatCommandRegistry,
    notebookTracker: INotebookTracker | null
  ) => {
    registry.addProvider(
      new SelectionCommandProvider(app.shell, notebookTracker!)
    );
  }
};
