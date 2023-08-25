import { EditorView } from '@codemirror/view';
/**
 * 添加旋转圆环加载动画到EditorView（codemirror 的 dom）左侧。
 *
 * @param view - ProseMirror的EditorView实例。
 */
export function addLoadingAnimation(view: EditorView): HTMLElement | null {
  removeLoadingAnimation(view);
  const cellNode = view.dom.closest('.jp-Cell');
  if (!cellNode) {
    return null;
  }

  const targetDiv = cellNode.querySelector(
    '.lm-Widget.jp-InputPrompt.jp-InputArea-prompt'
  );
  const circle = document.createElement('div');
  circle.className = 'circle-loading-animation';
  targetDiv?.appendChild(circle);

  return circle;
}

export function updateAnimation(
  view: EditorView,
  state: 'success' | 'failed'
): void {
  let circle = getLoadingCircle(view);
  if (!circle) {
    circle = addLoadingAnimation(view);
  }

  if (state === 'success') {
    circle?.classList.add('circle-success');
  } else if (state === 'failed') {
    circle?.classList.add('circle-failed');
  }

  setTimeout(() => {
    removeLoadingAnimation(view);
  }, 1500);
}

function getLoadingCircle(view: EditorView): HTMLElement | null | undefined {
  return view.dom
    .closest('.jp-Cell')
    ?.querySelector('.circle-loading-animation');
}

export const removeLoadingAnimation = (view: EditorView): void => {
  const circles = view.dom
    .closest('.jp-Cell')
    ?.querySelectorAll('.circle-loading-animation');
  circles?.forEach(circle => {
    circle.remove();
  });
};
