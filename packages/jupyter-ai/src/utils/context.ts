import { JupyterFrontEnd } from '@jupyterlab/application';
import { CodeEditor } from '@jupyterlab/codeeditor';
import { DocumentWidget } from '@jupyterlab/docregistry';
import { Notebook } from '@jupyterlab/notebook';
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

const getCellTextByBeforePointer = (editor: CodeEditor.IEditor): string[] => {
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

export const getCellTextByApp = (app: JupyterFrontEnd): string[] | null => {
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

export const getAllCellTextByPosition = (
  app: JupyterFrontEnd
): string[] | null => {
  const currentWidget = app.shell.currentWidget;
  if (!currentWidget || !(currentWidget instanceof DocumentWidget)) {
    return null;
  }

  const content = getContent(currentWidget);
  if (content instanceof Notebook) {
    const allCellText = [];
    const widgets = content.widgets;
    const activeCellIndex = content.activeCellIndex;

    // 遍历到当前单元格
    for (let index = 0; index <= activeCellIndex; index++) {
      const widget = widgets[index];
      const editor = widget.editor;
      if (editor) {
        // 如果是当前的单元格
        if (index === activeCellIndex) {
          const cellLines = getCellTextByBeforePointer(editor);
          allCellText.push(cellLines.join('\n'));
          break;
        }

        const text = getTextByEditor(editor);
        allCellText.push(text);
      }
    }
    return allCellText;
  }
  return null;
};
