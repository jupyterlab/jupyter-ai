import { JupyterFrontEnd, LabShell } from '@jupyterlab/application';
import { CodeMirrorEditor } from '@jupyterlab/codemirror';
import { keymap } from '@codemirror/view';
import { EditorView } from '@codemirror/view';
import { Prec } from '@codemirror/state';
import { StateEffect } from '@codemirror/state';
import { Notebook } from '@jupyterlab/notebook';
import { NotebookPanel } from '@jupyterlab/notebook';
import { Extension } from '@codemirror/state';
import { CodeEditor } from '@jupyterlab/codeeditor';

import { getContent } from './utils/instance';
import {
  codeCompletion,
  removeColor,
  handleAnyKeyPress
} from './bigcode/bigcode-code-completion';
import { parseKeyboardEventToShortcut } from './utils/keyboard';
import GlobalStore from './contexts/code-completion-context-store';

// Create a weak reference set to store the editor
const mountedEditors = new WeakSet<CodeMirrorEditor>();

/**
 * Mounts a given extension to the editor instance.
 * @param {CodeMirrorEditor} editor - The editor instance.
 * @param {Extension} extension - The extension to be mounted.
 */
const mountExtension = (
  editor: CodeMirrorEditor,
  extension: Extension
): void => {
  // If the editor has already been processed
  if (mountedEditors.has(editor)) {
    return;
  }

  // editor 还没有正常的完成初始化
  if (!('editor' in editor)) {
    return;
  }

  const view = editor.editor as EditorView;
  const tr = view.state.update({
    effects: StateEffect.appendConfig.of(extension)
  });

  view.dispatch(tr);
  mountedEditors.add(editor);
};

/**
 * Mounts the editor with a delay to ensure its instantiation is complete.
 * @param {CodeEditor.IEditor | null} editor - The editor instance, might be null.
 * @param {Extension} extension - The extension to be mounted.
 */
const mountEditorWithDelay = (
  editor: CodeEditor.IEditor | null,
  extension: Extension
) => {
  if (editor && editor instanceof CodeMirrorEditor) {
    const waitCellInitTimer = setTimeout(() => {
      const codeMirrorEditor = editor as CodeMirrorEditor;
      mountExtension(codeMirrorEditor, extension);
      clearTimeout(waitCellInitTimer);
    }, 0);
  }
};

/// Generates a keydown extension for handling various keypress events.
const generateKeyDownExtension = (app: JupyterFrontEnd): Extension => {
  return Prec.highest(
    keymap.of([
      {
        any: (view: EditorView, event: KeyboardEvent) => {
          const parsedShortcut = parseKeyboardEventToShortcut(event);
          console.debug('keyboard press: ', parsedShortcut);

          if (parsedShortcut === GlobalStore.shortcutStr) {
            console.debug('keyboard press: codeCompletion function is Running');
            return codeCompletion(app, view);
          }

          if (event.code === 'Enter') {
            console.debug('keyboard press: removeColor function is Running');
            return removeColor(view);
          }

          return handleAnyKeyPress(view);
        }
      }
    ])
  );
};

/**
 * Initializes keydown event handlers for the JupyterFrontEnd application.
 * This function sets up listeners for changes in the current widget and mounts the editor accordingly.
 * @param {JupyterFrontEnd} app - The JupyterFrontEnd application instance.
 */
const initializeKeyDownHandlers = (app: JupyterFrontEnd) => {
  if (!(app.shell instanceof LabShell)) {
    throw 'Shell is not an instance of LabShell. Jupyter AI does not currently support custom shells.';
  }

  const extension = generateKeyDownExtension(app);

  // Listen for changes in the current weiget
  app.shell.currentChanged.connect(async (sender, args) => {
    const currentWidget = args.newValue;
    if (!currentWidget || !(currentWidget instanceof NotebookPanel)) {
      return;
    }

    await currentWidget.context.ready;
    const content = getContent(currentWidget);

    if (content instanceof Notebook) {
      // Prioritize the cell selected by default when loading the notebook. In "content.activeCellChanged.connect", the editor of the cell selected by default is empty
      const firstCell = content.activeCell;
      if (firstCell) {
        const firstCellEditor = firstCell.editor as CodeMirrorEditor;
        mountEditorWithDelay(firstCellEditor, extension);
      }

      // When the selected cell changes
      content.activeCellChanged.connect(async (sender, cell) => {
        if (!cell) {
          return;
        }

        mountEditorWithDelay(cell.editor, extension);
      });
    }
  });
};

/**
 * The main function to handle code completion on keydown events.
 * It initializes the keydown handlers after ensuring that the notebook is fully loaded.
 * @param {JupyterFrontEnd} app - The JupyterFrontEnd application instance.
 * @returns {Promise<void>}
 */
export const handleCodeCompletionKeyDown = async (
  app: JupyterFrontEnd
): Promise<void> => {
  // Wait for the notebook to finish initializing
  await app.start();
  initializeKeyDownHandlers(app);
  console.log('handleCodeCompletionKeyDown is start...');
};
