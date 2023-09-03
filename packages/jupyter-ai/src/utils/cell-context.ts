import { JupyterFrontEnd } from '@jupyterlab/application';
import { CodeEditor } from '@jupyterlab/codeeditor';
import { DocumentWidget } from '@jupyterlab/docregistry';
import { Notebook } from '@jupyterlab/notebook';
import { CodeCell, MarkdownCell, Cell } from '@jupyterlab/cells';

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
 * Retrieves the output text from a given cell based on its type.
 *
 * The function extracts outputs from CodeCell instances based on their output type:
 * - For 'execute_result' type, it retrieves the data.
 * - For 'stream' type, it retrieves the text.
 * - For 'error' type, it retrieves the error value (evalue).
 *
 * If the cell is not an instance of CodeCell or has no valid output type, an empty string is returned.
 *
 * @param {Cell} cell - The cell from which to extract the output.
 * @returns {string} - The combined output text from the cell.
 */
const getCellOutput = (cell: Cell): string => {
  if (!(cell instanceof CodeCell)) {
    return '';
  }

  return cell.model.sharedModel.outputs.reduce((acc, output) => {
    console.log(output);
    switch (output.output_type) {
      case 'execute_result':
        if (output.data) {
          // Maybe there are other ways, but I didn't find it
          const outputData = JSON.parse(JSON.stringify(output.data));
          if ('text/plain' in outputData) {
            return acc + outputData['text/plain'];
          }
        }
        return output.data ? acc + JSON.stringify(output.data) : acc;
      case 'stream':
        return acc + output.text;
      case 'error':
        return acc + output.evalue;
      default:
        return acc;
    }
  }, '');
};

const getCellDetails = (cell: Cell, isActiveCell: boolean): ICell[] => {
  const cellType: ICellType =
    cell instanceof CodeCell
      ? 'code'
      : cell instanceof MarkdownCell
      ? 'markdown'
      : null;

  const results: ICell[] = [];

  const editor = cell.editor;
  if (editor) {
    const text = isActiveCell
      ? getTextBeforeCursor(editor).join('\n')
      : getTextByEditor(editor);
    results.push({ type: cellType, content: text });
  }

  results.push({ type: 'output', content: getCellOutput(cell) });

  return results;
};

/**
 * Retrieves all cell content up to the current active cell position.
 *
 * @param {JupyterFrontEnd} app - The JupyterFrontEnd application instance.
 * @returns {ICell[] | null} - An array of ICell objects with their content or null if not available.
 */
export const getNotebookContentUntilCursor = (
  app: JupyterFrontEnd
): ICell[] | null => {
  const currentWidget = app.shell.currentWidget;

  if (!currentWidget || !(currentWidget instanceof DocumentWidget)) {
    return null;
  }

  const content = getSpecificWidget(currentWidget);
  if (!(content instanceof Notebook)) {
    return null;
  }

  const activeCellIndex = content.activeCellIndex;

  const cellsUpToCursor = content.widgets
    .slice(0, activeCellIndex + 1)
    .flatMap((cell, index) => getCellDetails(cell, index === activeCellIndex));

  // Check if the last cell type is 'output' and remove it
  if (
    cellsUpToCursor.length > 0 &&
    cellsUpToCursor[cellsUpToCursor.length - 1].type === 'output'
  ) {
    cellsUpToCursor.pop();
  }

  return cellsUpToCursor;
};
