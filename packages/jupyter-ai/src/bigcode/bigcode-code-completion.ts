import { JupyterFrontEnd } from '@jupyterlab/application';
import { EditorView } from '@codemirror/view';
import { getAllCellTextByPosition } from '../utils/context';
import {
  sendToBigCode,
  processCompletionResult,
  constructContinuationPrompt
} from '../utils/bigcode-request';
import {
  insertAndHighlightCode,
  removeTextStatus,
  moveCursorToEnd,
  replaceText
} from '../utils/cell-modification';
import {
  addLoadingAnimation,
  updateAnimation,
  removeLoadingAnimation
} from '../utils/animation';
import { ICell } from '../types/cell';

import CodeCompletionContextstore from '../contexts/code-completion-context-store';

/**
 * An object to track the state of the request and the visibility of the result.
 * @property {boolean} loading - Indicates if a request is currently being made.
 * @property {boolean} viewResult - Indicates if the result of a request is currently being displayed.
 */
const requestState = {
  loading: false,
  viewResult: false
};

/**
 * Checks if the provided context is empty or not.
 * @param {ICell[]} context - An array of cells representing the context.
 * @returns {boolean} Returns true if the context is empty or undefined, otherwise false.
 */
const isContextEmpty = (context: ICell[]): boolean => {
  if (!context || context.length === 0) {
    return true; // If the context is empty or undefined, we assume that the user did not write code
  }

  const combinedContent = context.reduce((acc, cell) => acc + cell.content, '');
  return combinedContent.trim() === '';
};

/**
 * Handles the success response of the code completion request.
 * @param {JupyterFrontEnd} app - The JupyterFrontEnd application instance.
 * @param {EditorView} view - The editor view instance.
 * @param {{ generated_text: string }[]} result - The result array containing generated text.
 */
const requestSuccess = (
  app: JupyterFrontEnd,
  view: EditorView,
  result: { generated_text: string }[]
) => {
  const resultCode = processCompletionResult(result);
  requestState.viewResult = true;

  if (resultCode === '') {
    requestState.viewResult = false;
    CodeCompletionContextstore.setCodeOnRequest('');
  } else {
    insertAndHighlightCode(
      app,
      CodeCompletionContextstore.codeOnRequest,
      resultCode
    );
  }

  updateAnimation(view, 'success');
  requestState.loading = false;
};

/**
 * Handles the failure of the code completion request.
 * @param {EditorView} view - The editor view instance.
 */
const requestFailed = (view: EditorView) => {
  CodeCompletionContextstore.setCodeOnRequest('');

  updateAnimation(view, 'failed');
  requestState.viewResult = false;
  requestState.loading = false;
};

/**
 * Initiates code completion based on the provided context.
 * @param {JupyterFrontEnd} app - The JupyterFrontEnd application instance.
 * @param {EditorView} view - The editor view instance.
 * @returns {boolean} Indicates whether the function completed successfully.
 */
export const codeCompletion = (
  app: JupyterFrontEnd,
  view: EditorView
): boolean => {
  const context = getAllCellTextByPosition(app);
  if (!context || isContextEmpty(context)) {
    updateAnimation(view, 'failed');
    console.error('continueWriting() => context is null');
    return false;
  }

  if (requestState.loading || requestState.viewResult) {
    console.error('continueWriting() => request is running');
    return true;
  }

  console.debug('continueWriting() => context: ', context);

  requestState.loading = true;
  removeLoadingAnimation(view);
  addLoadingAnimation(view);
  CodeCompletionContextstore.setCodeOnRequest(
    context[context.length - 1].content
  );
  const prompt = constructContinuationPrompt(context);

  console.debug('codeCompletion() => prompt: ', prompt);

  sendToBigCode(prompt)
    .then(result => {
      console.debug('continueWriting() => state is success, result: ', result);
      requestSuccess(app, view, result);
    })
    .catch(async err => {
      console.error(await err);
      requestFailed(view);
    });

  return true;
};

/**
 * Removes custom colors from the text in the editor.
 * @param {EditorView} view - The editor view instance.
 * @returns {boolean} Indicates whether the function completed successfully.
 */
export const removeColor = (view: EditorView): boolean => {
  if (
    CodeCompletionContextstore.codeOnRequest === '' &&
    !requestState.viewResult
  ) {
    console.debug(
      'removeColor() => No request is running or no continuation code is showing'
    );
    return false;
  }

  requestState.viewResult = false;
  removeTextStatus(view);
  CodeCompletionContextstore.setCodeOnRequest('');
  moveCursorToEnd(view);
  console.debug('removeColor() => remove code customize color');
  return true;
};

/**
 * Handles any keypress events when a request is loading or a result is being displayed.
 * @param {EditorView} view - The editor view instance.
 * @returns {boolean} Indicates whether the function completed successfully.
 */
export const handleAnyKeyPress = (view: EditorView): boolean => {
  if (requestState.loading) {
    console.debug('handleAnyKeyPress() => request is loading');
    return true;
  }

  if (
    CodeCompletionContextstore.codeOnRequest !== '' ||
    requestState.viewResult
  ) {
    console.debug(
      'handleAnyKeyPress() => code for the user to cancel the display'
    );
    removeTextStatus(view);
    replaceText(view, CodeCompletionContextstore.codeOnRequest);
    CodeCompletionContextstore.setCodeOnRequest('');
    requestState.viewResult = false;
  }
  return false;
};
