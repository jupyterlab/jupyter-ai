import { JupyterFrontEnd, LabShell } from '@jupyterlab/application';
import { DocumentWidget } from '@jupyterlab/docregistry';
import { Widget } from '@lumino/widgets';
import { Signal } from '@lumino/signaling';

import { getEditor, getTextSelection } from './utils';

export class SelectionWatcher {
  constructor(shell: JupyterFrontEnd.IShell) {
    if (!(shell instanceof LabShell)) {
      throw 'Shell is not an instance of LabShell. Jupyter AI does not currently support custom shells.';
    }

    shell.currentChanged.connect((sender, args) => {
      this._mainAreaWidget = args.newValue;
    });
    setInterval(this._poll.bind(this), 200);
  }

  get selectionChanged() {
    return this._selectionChanged;
  }

  replaceSelection(value: string) {
    if (!(this._mainAreaWidget instanceof DocumentWidget)) {
      return;
    }

    const editor = getEditor(this._mainAreaWidget.content);
    editor?.replaceSelection?.(value);
  }

  protected _poll() {
    if (!(this._mainAreaWidget instanceof DocumentWidget)) {
      return;
    }

    const prevSelection = this._selection;
    const currSelection = getTextSelection(this._mainAreaWidget.content);

    if (prevSelection === currSelection) {
      return;
    }

    this._selection = currSelection;
    this._selectionChanged.emit(currSelection);
  }

  protected _mainAreaWidget: Widget | null = null;
  protected _selection = '';
  protected _selectionChanged = new Signal<this, string>(this);
}
