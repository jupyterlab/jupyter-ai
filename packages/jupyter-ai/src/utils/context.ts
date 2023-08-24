import { JupyterFrontEnd } from '@jupyterlab/application';
import { CodeEditor } from '@jupyterlab/codeeditor';
import { DocumentWidget } from '@jupyterlab/docregistry';

import { getTextByEditor, getContent, getEditorByWidget } from './instance';

export const splitString = (input: string): string[] => {
  // Split by newline, but ignore escaped newlines
  return input.split(/(?<!\\)\n/).map(part => part.replace('\\\\n', '\\n'));
};

export const getCellCode = (app: JupyterFrontEnd): string | null => {
  const currentWidget = app.shell.currentWidget;

  if (!currentWidget || !(currentWidget instanceof DocumentWidget)) {
    return null;
  }

  const content = getContent(currentWidget);
  const editor = getEditorByWidget(content);

  if (editor) {
    return getTextByEditor(editor);
  }

  return null;
};

export const getCellTextByBeforePointer = (
  editor: CodeEditor.IEditor
): string[] => {
  // Get the cursor position, e.g., {column: 2, line: 1}
  const position = editor.getCursorPosition();
  const text = getTextByEditor(editor);

  // Split by newline
  const codeLines = splitString(text);

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

export const getAllCellTextByBeforePointer = (
  app: JupyterFrontEnd
): string[] | null => {
  const currentWidget = app.shell.currentWidget;

  if (!currentWidget || !(currentWidget instanceof DocumentWidget)) {
    return null;
  }

  const content = getContent(currentWidget);
  const editor = getEditorByWidget(content);

  if (editor) {
    return getCellTextByBeforePointer(editor);
  }
  return null;
};
