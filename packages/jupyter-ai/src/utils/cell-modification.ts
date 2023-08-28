import { JupyterFrontEnd } from '@jupyterlab/application';
import { DocumentWidget } from '@jupyterlab/docregistry';
import { CodeMirrorEditor } from '@jupyterlab/codemirror';
import { EditorView } from '@codemirror/view';
import { StateEffect, StateField } from '@codemirror/state';
import { Decoration, DecorationSet } from '@codemirror/view';
import { CodeEditor } from '@jupyterlab/codeeditor';
import { splitString } from './cell-context';

/**
 * State effect definition for clearing text effects.
 */
const clearTextEffectState = StateEffect.define({});

/**
 * Removes any text status effects from the provided editor view.
 *
 * @param {EditorView} view - The EditorView instance where text statuses are to be removed.
 */
export function removeTextStatus(view: EditorView): void {
  view.dispatch({
    effects: clearTextEffectState.of(null)
  });
}

/**
 * Decoration definition for marking text with a 'gray-color' CSS class.
 */
const grayTextMark = Decoration.mark({ class: 'gray-color' });

/**
 * Base theme for gray text decorations.
 */
const grayTextTheme = EditorView.baseTheme({
  '.gray-color > span': { color: 'gray !important' },
  '.gray-color ': { color: 'gray !important' }
});

/**
 * State effect definition for changing the text status over a specified range.
 */
const changeRangeTextStatus = StateEffect.define<{ from: number; to: number }>({
  map: ({ from, to }, change) => ({
    from: change.mapPos(from),
    to: change.mapPos(to)
  })
});

/**
 * State field definition for tracking gray text decorations.
 */
const grayTextStateField = StateField.define<DecorationSet>({
  create() {
    return Decoration.none;
  },
  update(grayTexts, tr) {
    grayTexts = grayTexts.map(tr.changes);
    for (const e of tr.effects) {
      if (e.is(changeRangeTextStatus)) {
        grayTexts = grayTexts.update({
          add: [grayTextMark.range(e.value.from, e.value.to)]
        });
      }
    }
    if (tr.effects.some(e => e.is(clearTextEffectState))) {
      return Decoration.none;
    }

    return grayTexts;
  },
  provide: f => EditorView.decorations.from(f)
});

/**
 * Applies gray text decoration to a specified range within an editor view.
 *
 * @param {EditorView} view - The EditorView instance where the decoration is to be applied.
 * @param {number} start - The start position of the range.
 * @param {number} end - The end position of the range.
 * @returns {boolean} Indicates whether the operation was successful.
 */
export function applyGrayTextToSelection(
  view: EditorView,
  start: number,
  end: number
): boolean {
  if (start === end) {
    return false;
  }
  const effects: StateEffect<unknown>[] = [
    changeRangeTextStatus.of({ from: start, to: end })
  ];

  if (!view.state.field(grayTextStateField, false)) {
    effects.push(
      StateEffect.appendConfig.of([grayTextStateField, grayTextTheme])
    );
  }

  view.dispatch({ effects });
  return true;
}

/**
 * Calculates the line and column position of the cursor based on the provided code string.
 *
 * @param {string} code - The code string.
 * @returns {CodeEditor.IPosition} The calculated position of the cursor.
 */
export const calculatePointerPosition = (
  code: string
): CodeEditor.IPosition => {
  const lines = splitString(code);
  return {
    line: lines.length - 1,
    column: lines[lines.length - 1].length
  };
};

/**
 * Inserts the new code into the active cell of the Jupyter environment, highlighting the inserted portion.
 *
 * @param {JupyterFrontEnd} app - The JupyterFrontEnd application instance.
 * @param {string} oldCode - The original code string.
 * @param {string} newCode - The new code string to be appended.
 * @returns {boolean} Indicates whether the operation was successful.
 */
export const insertAndHighlightCode = (
  app: JupyterFrontEnd,
  oldCode: string,
  newCode: string
): boolean => {
  // Get the currently active document window
  const currentWidget = app.shell.currentWidget;
  if (!(currentWidget instanceof DocumentWidget)) {
    return false;
  }

  // content is also of type widget, just wrapped in a widget container
  const { content } = currentWidget;
  // The cell being currently operated on
  const activeCell = content.activeCell;
  // The CodeMirror instance object of the cell being currently operated on
  const editor = activeCell.editor as CodeMirrorEditor;
  if (editor) {
    const prePosition = calculatePointerPosition(oldCode);
    const view = editor.editor;
    // Update the current code
    editor.model.sharedModel.setSource(oldCode + newCode);

    // Restore the mouse pointer to its previous position, otherwise it will point to the 0 position
    editor.setCursorPosition(prePosition);

    // Change the color of the added code to gray
    return applyGrayTextToSelection(
      view,
      oldCode.length,
      (oldCode + newCode).length
    );
  }

  return false;
};

/**
 * Moves the cursor to the end of the document in the provided editor view.
 *
 * @param {EditorView} view - The EditorView instance where the cursor is to be moved.
 */
export const moveCursorToEnd = (view: EditorView): void => {
  const endPos = view.state.doc.length; // Get the document's length
  const transaction = view.state.update({
    selection: { anchor: endPos, head: endPos }, // Set both anchor and head to the end position
    scrollIntoView: true // Optionally scroll the view to show the cursor
  });

  view.dispatch(transaction);
};

/**
 * Replaces all the text in the provided editor view with the given new text.
 *
 * @param {EditorView} view - The EditorView instance where text is to be replaced.
 * @param {string} newText - The new text to replace the existing content.
 */
export const replaceText = (view: EditorView, newText: string): void => {
  // Create a new transaction to replace all text and move the cursor
  const tr = view.state.update({
    changes: { from: 0, to: view.state.doc.length, insert: newText }, // Replace all text with newText
    selection: { anchor: newText.length, head: newText.length }, // Move cursor to the end of newText
    scrollIntoView: true // Optionally scroll to show the cursor
  });

  view.dispatch(tr);
};
