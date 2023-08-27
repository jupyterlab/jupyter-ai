import { DocumentWidget } from '@jupyterlab/docregistry';
import { Widget } from '@lumino/widgets';
import { CodeEditor } from '@jupyterlab/codeeditor';
import { Notebook } from '@jupyterlab/notebook';

export const getSpecificWidget = (widget: DocumentWidget): Widget => {
  const { content } = widget;
  return content;
};

export const getEditorByWidget = (
  content: Widget
): CodeEditor.IEditor | null | undefined => {
  let editor: CodeEditor.IEditor | null | undefined;

  // Check if the content is an instance of a Notebook
  if (content instanceof Notebook) {
    editor = content.activeCell?.editor;
  }

  return editor;
};

export const getTextByEditor = (editor: CodeEditor.IEditor): string => {
  return editor.model.sharedModel.getSource();
};
