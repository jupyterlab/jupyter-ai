import React, { useState, useContext, useEffect } from 'react';

import { JupyterFrontEnd, LabShell } from '@jupyterlab/application';
import { DocumentWidget } from '@jupyterlab/docregistry';
import { Notebook, NotebookActions } from '@jupyterlab/notebook';
import { Cell } from '@jupyterlab/cells';

import { Widget } from '@lumino/widgets';
import { Signal } from '@lumino/signaling';

function getNotebook(widget: Widget | null): Notebook | null {
  if (!(widget instanceof DocumentWidget)) {
    return null;
  }

  const { content } = widget;
  if (!(content instanceof Notebook)) {
    return null;
  }

  return content;
}

function getActiveCell(widget: Widget | null): Cell | null {
  const notebook = getNotebook(widget);
  if (!notebook) {
    return null;
  }

  return notebook.activeCell;
}

/**
 * A manager that maintains a reference to the current active notebook cell in
 * the main panel (if any), and provides methods for inserting or appending
 * content to the active cell.
 *
 * The current active cell should be obtained by listening to the
 * `activeCellChanged` signal.
 */
export class ActiveCellManager {
  constructor(shell: JupyterFrontEnd.IShell) {
    if (!(shell instanceof LabShell)) {
      throw 'Shell is not an instance of LabShell. Jupyter AI does not currently support custom shells.';
    }

    this._shell = shell;
    this._shell.currentChanged.connect((sender, args) => {
      this._mainAreaWidget = args.newValue;
    });

    setInterval(this._updateActiveCell.bind(this), 200);
  }

  get activeCellChanged(): Signal<this, Cell | null> {
    return this._activeCellChanged;
  }

  /**
   * Inserts `content` in a new cell above the active cell.
   */
  insertAbove(content: string): void {
    const notebook = getNotebook(this._mainAreaWidget);
    if (!notebook) {
      return;
    }

    // create a new cell above the active cell and mark new cell as active
    NotebookActions.insertAbove(notebook);
    // emit activeCellChanged event to consumers
    this._updateActiveCell();
    // replace content of this new active cell
    this.replace(content);
  }

  /**
   * Inserts `content` in a new cell below the active cell.
   */
  insertBelow(content: string): void {
    const notebook = getNotebook(this._mainAreaWidget);
    if (!notebook) {
      return;
    }

    // create a new cell below the active cell and mark new cell as active
    NotebookActions.insertBelow(notebook);
    // emit activeCellChanged event to consumers
    this._updateActiveCell();
    // replace content of this new active cell
    this.replace(content);
  }

  /**
   * Replaces the contents of the active cell.
   */
  async replace(content: string): Promise<void> {
    // get reference to active cell directly from Notebook API. this avoids the
    // possibility of acting on an out-of-date reference.
    const activeCell = getNotebook(this._mainAreaWidget)?.activeCell;
    if (!activeCell) {
      return;
    }

    // wait for editor to be ready
    await activeCell.ready;

    // replace the content of the active cell
    /**
     * NOTE: calling this method sometimes emits an error to the browser console:
     *
     * ```
     * Error: Calls to EditorView.update are not allowed while an update is in progress
     * ```
     *
     * However, there seems to be no impact on the behavior/stability of the
     * JupyterLab application after this error is logged. Furthermore, this is
     * the official API for setting the content of a cell in JupyterLab 4,
     * meaning that this is likely unavoidable.
     */
    activeCell.editor?.model.sharedModel.setSource(content);
  }

  protected _updateActiveCell(): void {
    const prevActiveCell = this._activeCell;
    const currActiveCell = getActiveCell(this._mainAreaWidget);

    if (prevActiveCell === currActiveCell) {
      return;
    }

    this._activeCell = currActiveCell;
    this._activeCellChanged.emit(currActiveCell);
  }

  protected _shell: LabShell;
  protected _mainAreaWidget: Widget | null = null;
  protected _activeCell: Cell | null = null;
  protected _activeCellChanged = new Signal<this, Cell | null>(this);
}

const ActiveCellContext = React.createContext<
  [boolean, ActiveCellManager | null]
>([false, null]);

type ActiveCellContextProps = {
  activeCellManager: ActiveCellManager;
  children: React.ReactNode;
};

export function ActiveCellContextProvider(
  props: ActiveCellContextProps
): JSX.Element {
  const [activeCellExists, setActiveCellExists] = useState<boolean>(false);

  useEffect(() => {
    props.activeCellManager.activeCellChanged.connect((_, newActiveCell) => {
      setActiveCellExists(!!newActiveCell);
    });
  }, [props.activeCellManager]);

  return (
    <ActiveCellContext.Provider
      value={[activeCellExists, props.activeCellManager]}
    >
      {props.children}
    </ActiveCellContext.Provider>
  );
}

/**
 * Hook that returns the two-tuple `[activeCellExists, activeCellManager]`.
 */
export function useActiveCellContext(): [boolean, ActiveCellManager] {
  const [activeCellExists, activeCellManager] = useContext(ActiveCellContext);

  if (!activeCellManager) {
    throw new Error(
      'useActiveCellContext() cannot be called outside ActiveCellContextProvider.'
    );
  }

  return [activeCellExists, activeCellManager];
}
