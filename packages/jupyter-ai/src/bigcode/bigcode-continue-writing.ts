import { JupyterFrontEnd } from '@jupyterlab/application';
import { EditorView } from '@codemirror/view';
import { getAllCellTextByBeforePointer } from '../utils/context';
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
  requestSuccess as loadRequestSuccessAnimation,
  requestFailed as loadRequestFailedAnimation
} from '../utils/animation';

import GlobalStore from '../contexts/continue-writing-context';

const requestState = {
  loading: false,
  viewResult: false
};

const isContextEmpty = (context: string[]): boolean => {
  return context.every(code => code === '');
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

  loadRequestSuccessAnimation(view);
  requestState.loading = false;
};

const requestFailed = (view: EditorView) => {
  GlobalStore.setCodeOnRequest('');

  loadRequestFailedAnimation(view);
  requestState.viewResult = false;
  requestState.loading = false;
};

export const continueWriting = (
  app: JupyterFrontEnd,
  view: EditorView
): boolean => {
  const context = getAllCellTextByBeforePointer(app);
  if (!context) {
    return false;
  }

  if (isContextEmpty(context)) {
    loadRequestFailedAnimation(view);
    return false;
  }

  if (requestState.loading || requestState.viewResult) {
    return true;
  }

  requestState.loading = true;
  addLoadingAnimation(view);

  GlobalStore.setCodeOnRequest(context[context.length - 1]);
  const prompt = constructContinuationPrompt(context);

  sendToBigCode(prompt)
    .then(result => {
      requestSuccess(app, view, result);
    })
    .catch(err => {
      console.error(err);
      requestFailed(view);
    });

  return true;
};

export const removeColor = (view: EditorView): boolean => {
  if (GlobalStore.codeOnRequest === '') {
    return false;
  }

  requestState.viewResult = false;
  removeTextStatus(view);
  GlobalStore.setCodeOnRequest('');
  moveCursorToEnd(view);
  return true;
};

export const handleAnyKeyPress = (view: EditorView): boolean => {
  if (requestState.loading) {
    return true;
  }

  if (GlobalStore.codeOnRequest !== '') {
    removeTextStatus(view);
    replaceText(view, GlobalStore.codeOnRequest);
    GlobalStore.setCodeOnRequest('');
    requestState.viewResult = false;
  }

  return false;
};
