import { EditorView } from '@codemirror/view';

/**
 * Adds a rotating circle loading animation to the left side of the EditorView's DOM.
 * Removes any existing loading animations before adding a new one.
 *
 * @param {EditorView} view - The instance of ProseMirror's EditorView.
 * @returns {HTMLElement | null} The created circle animation element or null if the target div is not found.
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

/**
 * Updates the animation state to either 'success' or 'failed'.
 * If a loading circle doesn't exist, it will be created.
 *
 * @param {EditorView} view - The instance of ProseMirror's EditorView.
 * @param {('success' | 'failed')} state - The new state for the animation.
 */
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

  // It will disappear automatically after 1.5s
  setTimeout(() => {
    removeLoadingAnimation(view);
  }, 1500);
}

/**
 * Retrieves the loading circle from the closest cell of the given view.
 *
 * @param {EditorView} view - The instance of ProseMirror's EditorView.
 * @returns {HTMLElement | null | undefined} The loading circle element or null/undefined if not found.
 */
function getLoadingCircle(view: EditorView): HTMLElement | null | undefined {
  return view.dom
    .closest('.jp-Cell')
    ?.querySelector('.circle-loading-animation');
}

/**
 * Removes all loading/success/failed animations from the closest cell of the given view.
 *
 * @param {EditorView} view - The instance of ProseMirror's EditorView.
 */
export const removeLoadingAnimation = (view: EditorView): void => {
  const circles = view.dom
    .closest('.jp-Cell')
    ?.querySelectorAll('.circle-loading-animation');
  circles?.forEach(circle => {
    circle.remove();
  });
};
