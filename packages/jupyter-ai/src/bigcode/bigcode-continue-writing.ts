import { JupyterFrontEnd } from '@jupyterlab/application';
import { EditorView } from '@codemirror/view';
import { getAllCellTextByBeforePointer } from "../utils/context"
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
import { addLoadingAnimation, requestSuccess, requestFailed } from "../utils/animation"

import GlobalStore from '../contexts/continue-writing-context';
let isRequest: boolean = false;

export const continueWriting = (app: JupyterFrontEnd, view:EditorView): boolean => {
    const context = getAllCellTextByBeforePointer(app)
    if (!context) {
        return false
    }
    if (isContextEmpty(context)) {
        requestFailed(view)
        return false
    }
    if (isRequest) {
        console.log("多次")
        return true;
    }
    requestLoadingAnimation(view);
    isRequest = !isRequest
    addLoadingAnimation(view);

    GlobalStore.setCodeOnRequest(context[context.length - 1])
    const prompt = constructContinuationPrompt(context)

    sendToBigCode(prompt).then(result => {
        console.log(result)
        const resultCode = processCompletionResult(result)
        
        if (resultCode == ""){
            GlobalStore.setCodeOnRequest("")
        }else{
            insertAndHighlightCode(app, GlobalStore.codeOnRequest, resultCode)
        }

        isRequest = !isRequest
        requestSuccess(view)
        console.log("请求成功")
    }).catch(err=>{
        console.log(err)
        GlobalStore.setCodeOnRequest("")
        isRequest = !isRequest
        requestFailed(view)
    })

    return true;
}

const isContextEmpty = (context: string[]): boolean => {
    for(const code of context) {
        if (code != '') {
            return false;
        }
    }
    return true;
};

const requestLoadingAnimation = (view: EditorView) => {
    const circles = view.dom.closest('.jp-Cell')?.querySelectorAll('.circle-loading-animation');
    circles?.forEach(circle => {
        circle.remove();
    })
}

export const removeColor = (view: EditorView): boolean => {
    if (GlobalStore.codeOnRequest == "") {
        return false
    }

    removeTextStatus(view)
    GlobalStore.setCodeOnRequest("")
    moveCursorToEnd(view)
    return true
};

export const handleAnyKeyPress = (view: EditorView, event: KeyboardEvent) => {
    if (isRequest){
        return true
    }

    if (GlobalStore.codeOnRequest != "") {
        removeTextStatus(view)
        replaceText(view, GlobalStore.codeOnRequest)
        GlobalStore.setCodeOnRequest("")
    }

    return false
}