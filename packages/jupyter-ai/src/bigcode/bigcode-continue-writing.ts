import { JupyterFrontEnd } from '@jupyterlab/application';
import { EditorView } from '@codemirror/view';
import { getAllCellTextByBeforePointer } from "../utils/context"
import { sendToBigCode, processCompletionResult, constructContinuationPrompt } from "../utils/bigcode-request"
import { insertAndHighlightCode, removeTextStatus, moveCursorToEnd, replaceText } from "../utils/cell-modification"
import { addLoadingAnimation, requestSuccess, requestFailed } from "../utils/animation"

import GlobalStore from '../contexts/continue-writing-context';


export const continueWriting = (app: JupyterFrontEnd, view:EditorView): boolean => {
    const contexts = getAllCellTextByBeforePointer(app)
    if (!contexts) {
        return false
    }

    addLoadingAnimation(view);

    GlobalStore.setCodeOnRequest(contexts[contexts.length - 1])
    const prompt = constructContinuationPrompt(contexts)
    // 设置正在请求中
    GlobalStore.changeIsRequest();
    sendToBigCode(prompt).then(result => {
        const resultCode = processCompletionResult(result)

        if (resultCode == ""){
            GlobalStore.setCodeOnRequest("")
        }else{
            insertAndHighlightCode(app, GlobalStore.codeOnRequest, resultCode)
        }

        GlobalStore.changeIsRequest();
        requestSuccess(view)
    }).catch(err=>{
        console.log(err)
        GlobalStore.setCodeOnRequest("")
        GlobalStore.changeIsRequest();
        requestFailed(view)
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
}

export const handleAnyKeyPress = (view: EditorView, event: KeyboardEvent) => {
    if (GlobalStore.isRequest){
        return true
    }

    if (GlobalStore.codeOnRequest != "") {
        removeTextStatus(view)
        replaceText(view, GlobalStore.codeOnRequest)
        GlobalStore.setCodeOnRequest("")
    }

    return false
}