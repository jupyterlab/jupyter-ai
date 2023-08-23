import { JupyterFrontEnd } from '@jupyterlab/application';
// import { DocumentWidget } from '@jupyterlab/docregistry';
// import { CodeMirrorEditor } from "@jupyterlab/codemirror"
import { EditorView } from '@codemirror/view';
import { getAllCellTextByBeforePointer } from "../utils/context"
import { sendToBigCode, processCompletionResult, constructContinuationPrompt } from "../utils/bigcode-request"
import { insertAndHighlightCode, removeTextStatus, moveCursorToEnd, replaceText } from "../utils/cell-modification"

import GlobalStore from '../contexts/continue-writing-context';


export const continueWriting = (app: JupyterFrontEnd): boolean => {
    const contexts = getAllCellTextByBeforePointer(app)
    if (!contexts) {
        return false
    }

    GlobalStore.setCodeOnRequest(contexts[contexts.length - 1])
    const prompt = constructContinuationPrompt(contexts)

    sendToBigCode(prompt).then(result => {
        const resultCode = processCompletionResult(result)
        insertAndHighlightCode(app, GlobalStore.codeOnRequest, resultCode)
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
    if (GlobalStore.codeOnRequest != "") {
        removeTextStatus(view)
        replaceText(view, GlobalStore.codeOnRequest)
        GlobalStore.setCodeOnRequest("")
    }

    return false
}