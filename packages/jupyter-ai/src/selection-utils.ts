/**
 * Contains various utility functions used by the SelectionWatcher class.
 */
import { DocumentWidget } from '@jupyterlab/docregistry';
import { Notebook } from '@jupyterlab/notebook';
import { FileEditor } from '@jupyterlab/fileeditor';
import { CodeEditor } from '@jupyterlab/codeeditor';
import { CodeMirrorEditor } from '@jupyterlab/codemirror';
import { Widget } from '@lumino/widgets';

export type BaseSelection<T extends string extends T ? never : string> = {
  /**
   * Type of selection.
   */
  type: T;
  /**
   * The ID of the document widget in which the selection was made.
   */
  widgetId: string;
  /**
   * The ID of the cell in which the selection was made, if the original widget
   * was a notebook.
   */
  cellId?: string;
};

export type TextSelection = BaseSelection<'text'> &
  CodeEditor.ITextSelection & {
    /**
     * The text within the selection as a string.
     */
    text: string;
  };

/**
 * Represents a selection of one or more cells in a notebook.
 */
export type CellSelection = BaseSelection<'cell'> & {
  /**
   * The text within the selected cells represented as a string. Multiple cells
   * are joined with newlines.
   */
  text: string;
};

export type Selection = TextSelection | CellSelection;

/**
 * Gets the index of the cell associated with `cellId`.
 */
export function getCellIndex(notebook: Notebook, cellId: string): number {
  const idx = notebook.model?.sharedModel.cells.findIndex(
    cell => cell.getId() === cellId
  );
  return idx === undefined ? -1 : idx;
}

/**
 * Gets the editor instance used by a document widget. Returns `null` if unable.
 */
export function getEditor(widget: Widget | null): CodeMirrorEditor | null {
  if (!(widget instanceof DocumentWidget)) {
    return null;
  }

  let editor: CodeEditor.IEditor | undefined;
  const { content } = widget;

  if (content instanceof FileEditor) {
    editor = content.editor;
  } else if (content instanceof Notebook) {
    editor = content.activeCell?.editor;
  }

  if (!(editor instanceof CodeMirrorEditor)) {
    return null;
  }

  return editor;
}

/**
 * Gets a TextSelection object from a document widget. Returns `null` if unable.
 */
function getTextSelection(widget: DocumentWidget): Selection | null {
  const editor = getEditor(widget);
  // widget type check is redundant but hints the type to TypeScript
  if (!editor) {
    return null;
  }

  let cellId: string | undefined = undefined;
  if (widget.content instanceof Notebook) {
    cellId = widget.content.activeCell?.model.id;
  }

  let { start, end, ...selectionObj } = editor.getSelection();
  const startOffset = editor.getOffsetAt(start);
  const endOffset = editor.getOffsetAt(end);
  const text = editor.model.sharedModel
    .getSource()
    .substring(startOffset, endOffset);

  // ensure start <= end
  // required for editor.model.sharedModel.updateSource()
  if (startOffset > endOffset) {
    [start, end] = [end, start];
  }

  return {
    type: 'text',
    ...selectionObj,
    start,
    end,
    text,
    widgetId: widget.id,
    ...(cellId && {
      cellId
    })
  };
}

function getSelectedCells(notebook: Notebook) {
  return notebook.widgets.filter(cell => notebook.isSelected(cell));
}

function getCellSelection(widget: DocumentWidget): CellSelection | null {
  if (!(widget.content instanceof Notebook)) {
    return null;
  }

  const notebook = widget.content;
  const selectedCells = getSelectedCells(notebook);
  console.log({ selectedCells });

  const text = selectedCells.reduce<string>(
    (text: string, currCell) => text + '\n' + currCell.model.value,
    ''
  );
  console.log({ text });

  if (!text) {
    return null;
  }

  return {
    type: 'cell',
    widgetId: widget.id,
    text
  };
}

/**
 * Gets a Selection object from a document widget. Returns `null` if unable.
 */
export function getSelection(widget: Widget | null): Selection | null {
  if (!(widget instanceof DocumentWidget)) {
    return null;
  }

  const textSelection = getTextSelection(widget);
  if (textSelection) {
    return textSelection;
  }

  const cellSelection = getCellSelection(widget);
  if (cellSelection) {
    return cellSelection;
  }

  return null;
}
