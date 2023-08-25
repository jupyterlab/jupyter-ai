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

import GlobalStore from '../contexts/continue-writing-context';

const requestState = {
  loading: false,
  viewResult: false
};

const isContextEmpty = (context: ICell[]): boolean => {
  if (!context || context.length === 0) {
    return true; // 如果context为空或未定义，我们认为它是空的
  }

  const combinedContent = context.reduce((acc, cell) => acc + cell.content, '');
  return combinedContent.trim() === '';
};

const requestSuccess = (
  app: JupyterFrontEnd,
  view: EditorView,
  result: { generated_text: string }[]
) => {
  const resultCode = processCompletionResult(result);
  requestState.viewResult = true;

  if (resultCode === '') {
    requestState.viewResult = false;
    GlobalStore.setCodeOnRequest('');
  } else {
    insertAndHighlightCode(app, GlobalStore.codeOnRequest, resultCode);
  }

  updateAnimation(view, 'success');
  requestState.loading = false;
};

const requestFailed = (view: EditorView) => {
  GlobalStore.setCodeOnRequest('');

  updateAnimation(view, 'failed');
  requestState.viewResult = false;
  requestState.loading = false;
};

export const continueWriting = (
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
  GlobalStore.setCodeOnRequest(context[context.length - 1].content);
  const prompt = constructContinuationPrompt(context);

  console.debug('continueWriting() => prompt: ', prompt);

  sendToBigCode(prompt)
    .then(result => {
      console.debug('continueWriting() => state is success, result: ', result);
      requestSuccess(app, view, result);
    })
    .catch(err => {
      console.error(err);
      requestFailed(view);
    });

  return true;
};

export const removeColor = (view: EditorView): boolean => {
  if (GlobalStore.codeOnRequest === '' && !requestState.viewResult) {
    console.debug(
      'removeColor() => No request is running or no continuation code is showing'
    );
    return false;
  }

  requestState.viewResult = false;
  removeTextStatus(view);
  GlobalStore.setCodeOnRequest('');
  moveCursorToEnd(view);
  console.debug('removeColor() => remove code customize color');
  return true;
};

export const handleAnyKeyPress = (view: EditorView): boolean => {
  if (requestState.loading) {
    console.debug('handleAnyKeyPress() => request is loading');
    return true;
  }

  if (GlobalStore.codeOnRequest !== '' || requestState.viewResult) {
    console.debug(
      'handleAnyKeyPress() => code for the user to cancel the display'
    );
    removeTextStatus(view);
    replaceText(view, GlobalStore.codeOnRequest);
    GlobalStore.setCodeOnRequest('');
    requestState.viewResult = false;
  }
  return false;
};
