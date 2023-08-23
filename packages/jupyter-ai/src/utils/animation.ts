import { EditorView } from '@codemirror/view';
/**
 * 添加旋转圆环加载动画到EditorView左侧。
 * 
 * @param view - ProseMirror的EditorView实例。
 */
export function addLoadingAnimation(view: EditorView): void {
    // 获取单元格的DOM节点。
    const cellNode = view.dom.closest('.jp-Cell');

    if (!cellNode) return;
    const targetDiv = cellNode.querySelector('.lm-Widget.jp-InputPrompt.jp-InputArea-prompt');

    // 创建圆环元素并分配样式类名。
    const circle = document.createElement('div');
    circle.className = "circle-loading-animation";
    
    targetDiv?.appendChild(circle)
}


export function requestSuccess(view: EditorView): void {
    const circle = view.dom.closest('.jp-Cell')?.querySelector('.circle-loading-animation');
    if (!circle) return;

    // Update class for success state
    circle.classList.add("circle-success");
    
    // After the animation is complete, remove the circle
    setTimeout(() => {
        circle.remove();
    }, 1500);
}

export function requestFailed(view: EditorView): void {
    const circle = view.dom.closest('.jp-Cell')?.querySelector('.circle-loading-animation');
    if (!circle) return;

    // Update class for failed state
    circle.classList.add("circle-failed");

    // After the animation is complete, remove the circle
    setTimeout(() => {
        circle.remove();
    }, 1500);
}