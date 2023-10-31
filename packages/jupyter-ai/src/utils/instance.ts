import { DocumentWidget } from '@jupyterlab/docregistry';
import { Widget } from '@lumino/widgets';
import { CodeEditor } from '@jupyterlab/codeeditor';
import { Notebook } from '@jupyterlab/notebook';

/**
 * Extracts the content widget from a given DocumentWidget.
 *
 * @param {DocumentWidget} widget - The DocumentWidget instance from which the content is to be extracted.
 * @returns {Widget} - The content of the DocumentWidget.
 */
export const getSpecificWidget = (widget: DocumentWidget): Widget => {
  const { content } = widget;
  return content;
};

/**
 * Retrieves the editor associated with the provided content widget.
 *
 * This function aims to find the editor instance within different types of content widgets.
 * Currently, it supports extracting the editor from an active cell of a Notebook.
 * Further extensions can include more widget types and their respective logic to fetch the editor.
 *
 * @param {Widget} content - The content widget instance.
 * @returns {CodeEditor.IEditor | null | undefined} - The associated editor instance, or null/undefined if not found.
 */
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
