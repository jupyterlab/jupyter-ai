import { CodeEditor } from '@jupyterlab/codeeditor';
import { Notebook, NotebookPanel } from '@jupyterlab/notebook';
import { CodeCell, MarkdownCell, Cell } from '@jupyterlab/cells';

import { ICell, ICellType } from '../types/cell';

import { getSpecificWidget } from './instance';

/**
 * Retrieves the text content from a given editor.
 *
 * @param {CodeEditor.IEditor} editor - The editor instance.
 * @returns {string} - The text data of the current cell.
 */
const extractTextFromEditor = (editor: CodeEditor.IEditor): string => {
  return editor.model.sharedModel.getSource();
};

/**
 * Divides a string by lines, considering escaped newlines.
 *
 * @param {string} input - The string to split.
 * @returns {string[]} - An array of split lines.
 */
const divideStringByLines = (input: string): string[] => {
  // Split by newline, but ignore escaped newlines
  return input.split(/(?<!\\)\n/).map(part => part.replace('\\\\n', '\\n'));
};

/**
 * Fetches the text from an editor up to the current cursor's location.
 *
 * @param {CodeEditor.IEditor} editor - The editor instance.
 * @returns {string[]} - An array of lines up to the cursor position.
 */
const fetchTextUpToCursor = (editor: CodeEditor.IEditor): string[] => {
  // Get the cursor position, e.g. {column: 2, line: 1}
  const position = editor.getCursorPosition();
  const text = extractTextFromEditor(editor);
  // Split by newline
  const codeLines = divideStringByLines(text);

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
const extractOutputFromCell = (cell: Cell): string => {
  if (!(cell instanceof CodeCell)) {
    return '';
  }

  return cell.model.sharedModel.outputs.reduce((acc, output) => {
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

/**
 * Gathers details about a cell: its type, content, and output.
 *
 * @param cell - The target cell.
 * @param isCurrentlyActive - Whether the cell is the active one.
 * @returns An array of cell details.
 */
const gatherCellDetails = (cell: Cell, isActiveCell: boolean): ICell[] => {
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
      ? fetchTextUpToCursor(editor).join('\n')
      : extractTextFromEditor(editor);
    results.push({ type: cellType, content: text });
  }

  results.push({ type: 'output', content: extractOutputFromCell(cell) });

  return results;
};

/**
 * Fetches the content of the notebook up to the current cursor position.
 *
 * @param widget - The notebook panel widget.
 * @returns An array of cell contents up to the cursor, or null.
 */
export const retrieveNotebookContentUntilCursor = (
  widget: NotebookPanel
): ICell[] | null => {
  const content = getSpecificWidget(widget);
  if (!(content instanceof Notebook)) {
    return null;
  }

  const activeCellIndex = content.activeCellIndex;

  const cellsUpToCursor = content.widgets
    .slice(0, activeCellIndex + 1)
    .flatMap((cell, index) =>
      gatherCellDetails(cell, index === activeCellIndex)
    );

  // Check if the last cell type is 'output' and remove it
  if (
    cellsUpToCursor.length > 0 &&
    cellsUpToCursor[cellsUpToCursor.length - 1].type === 'output'
  ) {
    cellsUpToCursor.pop();
  }

  return cellsUpToCursor;
};
