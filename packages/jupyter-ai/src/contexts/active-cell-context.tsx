import React, { useState, useContext, useEffect } from 'react';

import { JupyterFrontEnd } from '@jupyterlab/application';
import { DocumentWidget } from '@jupyterlab/docregistry';
import { Notebook, NotebookActions } from '@jupyterlab/notebook';
import { Cell } from '@jupyterlab/cells';
import { IError as CellError } from '@jupyterlab/nbformat';

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

type CellContent = {
  type: string;
  source: string;
};

type CellWithErrorContent = {
  type: 'code';
  source: string;
  error: {
    name: string;
    value: string;
    traceback: string[];
  };
};

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
    this._shell = shell;
    this._shell.currentChanged?.connect((sender, args) => {
      this._mainAreaWidget = args.newValue;
    });

    setInterval(() => {
      this._pollActiveCell();
    }, 200);
  }

  get activeCellChanged(): Signal<this, Cell | null> {
    return this._activeCellChanged;
  }

  get activeCellErrorChanged(): Signal<this, CellError | null> {
    return this._activeCellErrorChanged;
  }

  /**
   * Returns an `ActiveCellContent` object that describes the current active
   * cell. If no active cell exists, this method returns `null`.
   *
   * When called with `withError = true`, this method returns `null` if the
   * active cell does not have an error output. Otherwise it returns an
   * `ActiveCellContentWithError` object that describes both the active cell and
   * the error output.
   */
  getContent(withError: false): CellContent | null;
  getContent(withError: true): CellWithErrorContent | null;
  getContent(withError = false): CellContent | CellWithErrorContent | null {
    const sharedModel = this._activeCell?.model.sharedModel;
    if (!sharedModel) {
      return null;
    }

    // case where withError = false
    if (!withError) {
      return {
        type: sharedModel.cell_type,
        source: sharedModel.getSource()
      };
    }

    // case where withError = true
    const error = this._activeCellError;
    if (error) {
      return {
        type: 'code',
        source: sharedModel.getSource(),
        error: {
          name: error.ename,
          value: error.evalue,
          traceback: error.traceback
        }
      };
    }

    return null;
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
    this._pollActiveCell();
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
    this._pollActiveCell();
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

  protected _pollActiveCell(): void {
    const prevActiveCell = this._activeCell;
    const currActiveCell = getActiveCell(this._mainAreaWidget);

    // emit activeCellChanged when active cell changes
    if (prevActiveCell !== currActiveCell) {
      this._activeCell = currActiveCell;
      this._activeCellChanged.emit(currActiveCell);
    }

    const currSharedModel = currActiveCell?.model.sharedModel;
    const prevExecutionCount = this._activeCellExecutionCount;
    const currExecutionCount: number | null =
      currSharedModel && 'execution_count' in currSharedModel
        ? currSharedModel?.execution_count
        : null;
    this._activeCellExecutionCount = currExecutionCount;

    // emit activeCellErrorChanged when active cell changes or when the
    // execution count changes
    if (
      prevActiveCell !== currActiveCell ||
      prevExecutionCount !== currExecutionCount
    ) {
      const prevActiveCellError = this._activeCellError;
      let currActiveCellError: CellError | null = null;
      if (currSharedModel && 'outputs' in currSharedModel) {
        currActiveCellError =
          currSharedModel.outputs.find<CellError>(
            (output): output is CellError => output.output_type === 'error'
          ) || null;
      }

      // for some reason, the `CellError` object is not referentially stable,
      // meaning that this condition always evaluates to `true` and the
      // `activeCellErrorChanged` signal is emitted every 200ms, even when the
      // error output is unchanged. this is why we have to rely on
      // `execution_count` to track changes to the error output.
      if (prevActiveCellError !== currActiveCellError) {
        this._activeCellError = currActiveCellError;
        this._activeCellErrorChanged.emit(this._activeCellError);
      }
    }
  }

  protected _shell: JupyterFrontEnd.IShell;
  protected _mainAreaWidget: Widget | null = null;

  /**
   * The active cell.
   */
  protected _activeCell: Cell | null = null;
  /**
   * The execution count of the active cell. This is the number shown on the
   * left in square brackets after running a cell. Changes to this indicate that
   * the error output may have changed.
   */
  protected _activeCellExecutionCount: number | null = null;
  /**
   * The `CellError` output within the active cell, if any.
   */
  protected _activeCellError: CellError | null = null;

  protected _activeCellChanged = new Signal<this, Cell | null>(this);
  protected _activeCellErrorChanged = new Signal<this, CellError | null>(this);
}

type ActiveCellContextReturn = {
  exists: boolean;
  hasError: boolean;
  manager: ActiveCellManager;
};

type ActiveCellContextValue = {
  exists: boolean;
  hasError: boolean;
  manager: ActiveCellManager | null;
};

const defaultActiveCellContext: ActiveCellContextValue = {
  exists: false,
  hasError: false,
  manager: null
};

const ActiveCellContext = React.createContext<ActiveCellContextValue>(
  defaultActiveCellContext
);

type ActiveCellContextProps = {
  activeCellManager: ActiveCellManager;
  children: React.ReactNode;
};

export function ActiveCellContextProvider(
  props: ActiveCellContextProps
): JSX.Element {
  const [exists, setExists] = useState<boolean>(false);
  const [hasError, setHasError] = useState<boolean>(false);

  useEffect(() => {
    const manager = props.activeCellManager;

    manager.activeCellChanged.connect((_, newActiveCell) => {
      setExists(!!newActiveCell);
    });
    manager.activeCellErrorChanged.connect((_, newActiveCellError) => {
      setHasError(!!newActiveCellError);
    });
  }, [props.activeCellManager]);

  return (
    <ActiveCellContext.Provider
      value={{
        exists,
        hasError,
        manager: props.activeCellManager
      }}
    >
      {props.children}
    </ActiveCellContext.Provider>
  );
}

/**
 * Usage: `const activeCell = useActiveCellContext()`
 *
 * Returns an object `activeCell` with the following properties:
 * - `activeCell.exists`: whether an active cell exists
 * - `activeCell.hasError`: whether an active cell exists with an error output
 * - `activeCell.manager`: the `ActiveCellManager` singleton
 */
export function useActiveCellContext(): ActiveCellContextReturn {
  const { exists, hasError, manager } = useContext(ActiveCellContext);

  if (!manager) {
    throw new Error(
      'useActiveCellContext() cannot be called outside ActiveCellContextProvider.'
    );
  }

  return {
    exists,
    hasError,
    manager
  };
}
