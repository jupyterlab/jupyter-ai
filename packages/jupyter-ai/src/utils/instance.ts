import { DocumentWidget } from '@jupyterlab/docregistry';
import { Widget } from '@lumino/widgets';


export const getContent = (widget: DocumentWidget): Widget => {
    const { content } = widget;
    return content;
};