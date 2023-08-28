import { JupyterFrontEnd } from '@jupyterlab/application';
import { CodeEditor } from '@jupyterlab/codeeditor';
import { DocumentWidget } from '@jupyterlab/docregistry';
import { Notebook } from '@jupyterlab/notebook';
import { CodeCell, MarkdownCell } from '@jupyterlab/cells';

import { ICell, ICellType } from '../types/cell';

import { getSpecificWidget, getEditorByWidget } from './instance';

/**
 * Get the text from the current editor.
 *
 * @param {CodeEditor.IEditor} editor - The editor instance.
 * @returns {string} - The text data of the current cell.
 */
export const getTextByEditor = (editor: CodeEditor.IEditor): string => {
  return editor.model.sharedModel.getSource();
};

/**
 * Splits a string into lines, accounting for escaped newlines.
 *
 * @param {string} input - The string to split.
 * @returns {string[]} - An array of split lines.
 */
export const splitString = (input: string): string[] => {
  // Split by newline, but ignore escaped newlines
  return input.split(/(?<!\\)\n/).map(part => part.replace('\\\\n', '\\n'));
};

/**
 * Retrieves the code of the current cell in the Jupyter environment.
 *
 * @param {JupyterFrontEnd} app - The JupyterFrontEnd application instance.
 * @returns {string | null} - The code from the current cell or null if not available.
 */
export const getCellCode = (app: JupyterFrontEnd): string | null => {
  const currentWidget = app.shell.currentWidget;

  if (!currentWidget || !(currentWidget instanceof DocumentWidget)) {
    return null;
  }

  const content = getSpecificWidget(currentWidget);
  const editor = getEditorByWidget(content);

  if (editor) {
    return getTextByEditor(editor);
  }

  return null;
};

/**
 * Gets the text from the current editor up to the current cursor position.
 *
 * @param {CodeEditor.IEditor} editor - The editor instance.
 * @returns {string[]} - An array of lines up to the cursor position.
 */
const getTextBeforeCursor = (editor: CodeEditor.IEditor): string[] => {
  // Get the cursor position, e.g. {column: 2, line: 1}
  const position = editor.getCursorPosition();
  const text = getTextByEditor(editor);
  // Split by newline
  const codeLines = splitString(text);

  const codeLinesPositionBefore = [];
  // Iterate from the first cell to the position of the active cell
  for (let index = 0; index <= position.line; index++) {
    // If iterating to the current cell
    if (index === position.line) {
      codeLinesPositionBefore.push(codeLines[index].slice(0, position.column));
      continue;
    }

    codeLinesPositionBefore.push(codeLines[index]);
  }

  return codeLinesPositionBefore;
};

/**
 * Retrieves the text of the current cell up to the cursor position.
 *
 * @param {JupyterFrontEnd} app - The JupyterFrontEnd application instance.
 * @returns {string[] | null} - An array of lines up to the cursor position or null if not available.
 */
export const getTextBeforeCursorFromApp = (
  app: JupyterFrontEnd
): string[] | null => {
  const currentWidget = app.shell.currentWidget;

  if (!currentWidget || !(currentWidget instanceof DocumentWidget)) {
    return null;
  }

  const content = getSpecificWidget(currentWidget);
  const editor = getEditorByWidget(content);

  if (editor) {
    return getTextBeforeCursor(editor);
  }

  return null;
};

/**
 * Retrieves all cell content up to the current active cell position.
 *
 * @param {JupyterFrontEnd} app - The JupyterFrontEnd application instance.
 * @returns {ICell[] | null} - An array of ICell objects with their content or null if not available.
 */
export const getTextInActiveCellUpToCursor = (
  app: JupyterFrontEnd
): ICell[] | null => {
  const currentWidget = app.shell.currentWidget;
  if (!currentWidget || !(currentWidget instanceof DocumentWidget)) {
    return null;
  }

  const content = getSpecificWidget(currentWidget);
  if (content instanceof Notebook) {
    const allCellBase: ICell[] = [];
    const widgets = content.widgets;
    const activeCellIndex = content.activeCellIndex;

    // traverse to the current cell
    for (let index = 0; index <= activeCellIndex; index++) {
      const widget = widgets[index];
      const cellType: ICellType =
        widget instanceof CodeCell
          ? 'code'
          : widget instanceof MarkdownCell
          ? 'markdown'
          : null;

      const editor = widget.editor;
      if (editor) {
        // If the current cell
        if (index === activeCellIndex) {
          const cellLines = getTextBeforeCursor(editor);
          allCellBase.push({
            type: cellType,
            content: cellLines.join('\n')
          });
          break;
        }

        const codeText = getTextByEditor(editor);
        allCellBase.push({
          type: cellType,
          content: codeText
        });
      }
    }
    return allCellBase;
  }
  return null;
};
