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

const isContextEmpty = (context: string[]): boolean => {
    for(const code of context) {
        if (code != '') {
            return false;
        }
    }
    return true;
};

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
        return true;
    }

    isRequest = true;
    addLoadingAnimation(view);

    GlobalStore.setCodeOnRequest(context[context.length - 1])
    const prompt = constructContinuationPrompt(context)

    sendToBigCode(prompt).then(result => {
        const resultCode = processCompletionResult(result)
        
        if (resultCode == ""){
            GlobalStore.setCodeOnRequest("")
        }else{
            insertAndHighlightCode(app, GlobalStore.codeOnRequest, resultCode)
        }

        requestSuccess(view)
        isRequest = false
    }).catch(err=>{
        console.error(err)
        GlobalStore.setCodeOnRequest("")
        
        requestFailed(view)
        isRequest = false
    })

    return true;
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