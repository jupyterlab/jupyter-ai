import { JupyterFrontEnd, LabShell } from '@jupyterlab/application';
import { DocumentWidget } from '@jupyterlab/docregistry';
import { Notebook } from '@jupyterlab/notebook';

import { find } from '@lumino/algorithm';
import { Widget } from '@lumino/widgets';
import { Signal } from '@lumino/signaling';

import type { Selection, TextSelection } from './selection-utils';
import { getCellIndex, getEditor, getSelection } from './selection-utils';

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

  replaceSelection(selection: TextSelection) {
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
    const currSelection = getSelection(this._mainAreaWidget);

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
