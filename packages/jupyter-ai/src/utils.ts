/**
 * Contains various utility functions shared throughout the project.
 */
import { INotebookTracker, Notebook } from '@jupyterlab/notebook';
import { FileEditor } from '@jupyterlab/fileeditor';
import { CodeEditor } from '@jupyterlab/codeeditor';
import { Widget } from '@lumino/widgets';
import { IKernelConnection } from '@jupyterlab/services/lib/kernel/kernel';
import { IIOPubMessage } from '@jupyterlab/services/lib/kernel/messages';
import { CellModel } from '@jupyterlab/cells';

/**
 * Get text selection from an editor widget (DocumentWidget#content).
 */
export function getTextSelection(widget: Widget): string {
  const editor = getEditor(widget);
  if (!editor) {
    return '';
  }

  const selectionObj = editor.getSelection();
  const start = editor.getOffsetAt(selectionObj.start);
  const end = editor.getOffsetAt(selectionObj.end);
  const text = editor.model.sharedModel.getSource().substring(start, end);

  return text;
}

/**
 * Get editor instance from an editor widget (i.e. `DocumentWidget#content`).
 */
export function getEditor(
  widget: Widget
): CodeEditor.IEditor | null | undefined {
  let editor: CodeEditor.IEditor | null | undefined;
  if (widget instanceof FileEditor) {
    editor = widget.editor;
  } else if (widget instanceof Notebook) {
    editor = widget.activeCell?.editor;
  }

  return editor;
}

/**
 * Gets the index of the cell associated with `cellId`.
 */
export function getCellIndex(notebook: Notebook, cellId: string): number {
  const idx = notebook.model?.sharedModel.cells.findIndex(
    cell => cell.getId() === cellId
  );
  return idx === undefined ? -1 : idx;
}

/**
 * Obtain the provider ID component from a model ID.
 */
export function getProviderId(globalModelId: string): string | null {
  if (!globalModelId) {
    return null;
  }

  return globalModelId.split(':')[0];
}

/**
 * Obtain the model name component from a model ID.
 */
export function getModelLocalId(globalModelId: string): string | null {
  if (!globalModelId) {
    return null;
  }

  const components = globalModelId.split(':').slice(1);
  return components.join(':');
}

/**
 * Executes a given code string in the provided Jupyter Notebook kernel and retrieves the output.
 *
 * @param kernel - The kernel connection to execute the code.
 * @param code - The code string to be executed.
 * @returns A promise that resolves with the output of the executed code or null if the execution fails.
 */
export async function executeCode(kernel: IKernelConnection, code: string): Promise<string | null> {
    const executeRequest = kernel.requestExecute({ code });
    let variableValue: string | null = null;

    kernel.registerMessageHook(executeRequest.msg.header.msg_id, (msg: IIOPubMessage) => {
      if (
        msg.header.msg_type === 'stream' &&
        // @ts-expect-error tserror
        msg.content.name === 'stdout'
      ) {
        // @ts-expect-error tserror
        variableValue = msg.content.text.trim();
      }
      return true;
    });

    const reply = await executeRequest.done;
    if (reply && reply.content.status === 'ok') {
      return variableValue;
    } else {
      console.error('Failed to retrieve variable value');
      return null;
    }
}

/**
 * Generates the code to describe a variable using a Jupyter AI utility.
 *
 * @param name - The name of the variable to describe.
 * @returns The generated code as a string.
 */
const getCode = (name: string) => `
from jupyter_ai._variable_describer import describe_var
print(describe_var('${name}', ${name}))
`

/**
 * Retrieves the description of a variable from the current Jupyter Notebook kernel.
 *
 * @param variableName - The name of the variable to describe.
 * @param notebookTracker - The notebook tracker to get the current notebook and kernel.
 * @returns A promise that resolves with the variable description or null if retrieval fails.
 */
export async function getVariableDescription(
    variableName: string,
    notebookTracker: INotebookTracker
): Promise<string | null> {
    const notebook = notebookTracker.currentWidget;
    if (notebook && notebook.sessionContext.session?.kernel) {
        const kernel = notebook.sessionContext.session.kernel;
        try {
        return await executeCode(kernel, getCode(variableName));
        } catch (error) {
        console.error('Error retrieving variable value:', error);
        return null;
        }
    } else {
        console.error('No active kernel found');
        return null;
    }
}

/**
 * Processes variables in the user input by replacing them with their descriptions from the Jupyter Notebook kernel.
 *
 * @param userInput - The user input string containing variables to process.
 * @param notebookTracker - The notebook tracker to get the current notebook and kernel.
 * @returns A promise that resolves with an object containing the processed input and variable values.
 */
export async function processVariables(
    userInput: string,
    notebookTracker: INotebookTracker | null
  ): Promise<{
    processedInput: string,
    varValues: string
  }> {
    if (!notebookTracker) {
        return {
            processedInput: userInput,
            varValues: ""
        }
    }

    const variablePattern = / @([a-zA-Z_][a-zA-Z0-9_]*(\[[^\]]+\]|(\.[a-zA-Z_][a-zA-Z0-9_]*)?)*)[\s,\-]?/g;
    let match;
    let variablesProcessed: string[] = [];
    let varValues = '';
    let processedInput = userInput;

    while ((match = variablePattern.exec(userInput)) !== null) {
      const variableName = match[1];
      if (variablesProcessed.includes(variableName)) {
        continue;
      }
      variablesProcessed.push(variableName);
      try {
        const varDescription = await getVariableDescription(variableName, notebookTracker);
        varValues += `${varDescription}`;
        processedInput = processedInput.replace(`@${variableName}`, `\`${variableName}\``);
    } catch (error) {
        console.error(`Error accessing variable ${variableName}:`, error);
      }
    }

    return { processedInput, varValues}
  }

/**
 * Code to retrieve the global variables from the Jupyter Notebook kernel.
 */
const GLOBALS_CODE = `
from jupyter_ai.filter_autocomplete_globals import filter_globals
print(filter_globals(globals()))
`

/**
 * Retrieves completion suggestions for a given prefix from the current Jupyter Notebook kernel's global variables.
 *
 * @param prefix - The prefix to match global variables against.
 * @param notebookTracker - The notebook tracker to get the current notebook and kernel.
 * @returns A promise that resolves with an array of matching global variable names.
 */
export async function getCompletion(
    prefix: string,
    notebookTracker: INotebookTracker | null
): Promise<string[]> {
    const notebook = notebookTracker?.currentWidget;
    if (notebook?.sessionContext?.session?.kernel) {
        const kernel = notebook.sessionContext.session.kernel;
        const globalsString = await executeCode(kernel, GLOBALS_CODE);

        if (!globalsString) return [];

        const globals: string[] = JSON.parse(globalsString.replace(/'/g, '"'));
        const filteredGlobals = globals.filter(x => x.startsWith(prefix))


        return filteredGlobals;
    }

    return [];
}

/**
 * Formats code for a Jupyter Notebook cell, adding appropriate annotations based on cell type.
 *
 * @param cell - The cell model containing the code to format.
 * @param index - Optional index of the cell for annotation.
 * @returns The formatted code as a string.
 */
export const formatCodeForCell = (cell: CellModel["sharedModel"], index?: number) => {
    const cellNumber = index !== undefined ? `Cell ${index}` : '';

    switch (cell.cell_type) {
        case "code":
            return `# %% ${cellNumber}\n${cell.source}`
        case "markdown":
        case "raw":
            const source = cell.source.split("\n").map(line => `# ${line}`).join("\n")
            return `# %% [markdown] ${cellNumber}\n${source}`
        default:
            return ""
    }
  }