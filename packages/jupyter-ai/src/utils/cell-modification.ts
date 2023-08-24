import { JupyterFrontEnd } from '@jupyterlab/application';
import { DocumentWidget } from '@jupyterlab/docregistry';
import { CodeMirrorEditor } from '@jupyterlab/codemirror';
import { EditorView } from '@codemirror/view';
import { StateEffect, StateField } from '@codemirror/state';
import { Decoration, DecorationSet } from '@codemirror/view';
import { CodeEditor } from '@jupyterlab/codeeditor';
import { splitString } from './context';

const clearTextEffectState = StateEffect.define({});

export function removeTextStatus(view: EditorView): void {
  view.dispatch({
    effects: clearTextEffectState.of(null)
  });
}

// Create a mark status (meaning we've marked a string, so the class of this string's DOM is "gray-color")
const grayTextMark = Decoration.mark({ class: 'gray-color' });

// Marked css theme
const grayTextTheme = EditorView.baseTheme({
  '.gray-color > span': { color: 'gray !important' },
  '.gray-color ': { color: 'gray !important' }
});

// Container to save the characters and theme we need to change (we need to first calculate which characters are what we need)
const changeRangeTextStatus = StateEffect.define<{ from: number; to: number }>({
  map: ({ from, to }, change) => ({
    from: change.mapPos(from),
    to: change.mapPos(to)
  })
});

// codemirror's editorView extension
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

// Change the specified range of characters in EditorView to gray
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

export const calculatePointerPosition = (
  code: string
): CodeEditor.IPosition => {
  const lines = splitString(code);
  return {
    line: lines.length - 1,
    column: lines[lines.length - 1].length
  };
};

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

export const moveCursorToEnd = (view: EditorView): void => {
  const endPos = view.state.doc.length; // Get the document's length
  const transaction = view.state.update({
    selection: { anchor: endPos, head: endPos }, // Set both anchor and head to the end position
    scrollIntoView: true // Optionally scroll the view to show the cursor
  });

  view.dispatch(transaction);
};

export const replaceText = (view: EditorView, newText: string): void => {
  // Create a new transaction to replace all text and move the cursor
  const tr = view.state.update({
    changes: { from: 0, to: view.state.doc.length, insert: newText }, // Replace all text with newText
    selection: { anchor: newText.length, head: newText.length }, // Move cursor to the end of newText
    scrollIntoView: true // Optionally scroll to show the cursor
  });

  view.dispatch(tr);
};
