import { JupyterFrontEnd, LabShell } from '@jupyterlab/application';
import { DocumentWidget } from '@jupyterlab/docregistry';
import { CodeEditor } from '@jupyterlab/codeeditor';
import { CodeMirrorEditor } from '@jupyterlab/codemirror';
import { FileEditor } from '@jupyterlab/fileeditor';
import { Notebook } from '@jupyterlab/notebook';

import { find } from '@lumino/algorithm';
import { Widget } from '@lumino/widgets';
import { Signal } from '@lumino/signaling';

import { getCellIndex } from './utils';

/**
 * Gets the editor instance used by a document widget. Returns `null` if unable.
 */
function getEditor(widget: Widget | null) {
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
    return undefined;
  }

  return editor;
}

/**
 * Gets a Selection object from a document widget. Returns `null` if unable.
 */
function getTextSelection(widget: Widget | null): Selection | null {
  const editor = getEditor(widget);
  // widget type check is redundant but hints the type to TypeScript
  if (!editor || !(widget instanceof DocumentWidget)) {
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

export type Selection = CodeEditor.ITextSelection & {
  /**
   * The text within the selection as a string.
   */
  text: string;
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

export class SelectionWatcher {
  constructor(shell: JupyterFrontEnd.IShell) {
    if (!(shell instanceof LabShell)) {
      throw 'Shell is not an instance of LabShell. Jupyter AI does not currently support custom shells.';
    }

    this._shell = shell;
    this._shell.currentChanged.connect((sender, args) => {
      this._mainAreaWidget = args.newValue;
    });

    setInterval(this._poll.bind(this), 200);
  }

  get selectionChanged() {
    return this._selectionChanged;
  }

  replaceSelection(selection: Selection) {
    // unfortunately shell.currentWidget doesn't update synchronously after
    // shell.activateById(), which is why we have to get a reference to the
    // widget manually.
    const widget = find(
      this._shell.widgets(),
      widget => widget.id === selection.widgetId
    );
    if (!(widget instanceof DocumentWidget)) {
      return;
    }

    // activate the widget if not already active
    this._shell.activateById(selection.widgetId);

    // activate notebook cell if specified
    if (widget.content instanceof Notebook && selection.cellId) {
      const cellIndex = getCellIndex(widget.content, selection.cellId);
      if (cellIndex !== -1) {
        widget.content.activeCellIndex = cellIndex;
      }
    }

    // get editor instance
    const editor = getEditor(widget);
    if (!editor) {
      return;
    }

    editor.model.sharedModel.updateSource(
      editor.getOffsetAt(selection.start),
      editor.getOffsetAt(selection.end),
      selection.text
    );
    const newPosition = editor.getPositionAt(
      editor.getOffsetAt(selection.start) + selection.text.length
    );
    editor.setSelection({ start: newPosition, end: newPosition });
  }

  protected _poll() {
    const prevSelection = this._selection;
    const currSelection = getTextSelection(this._mainAreaWidget);

    if (prevSelection?.text === currSelection?.text) {
      return;
    }

    this._selection = currSelection;
    this._selectionChanged.emit(currSelection);
  }

  protected _shell: LabShell;
  protected _mainAreaWidget: Widget | null = null;
  protected _selection: Selection | null = null;
  protected _selectionChanged = new Signal<this, Selection | null>(this);
}
