import { useActiveCellContext } from '../contexts/active-cell-context';
import { useSelectionContext } from '../contexts/selection-context';

export type UseReplaceReturn = {
  /**
   * If a user has a range of text selected, this function replaces the
   * selection range with `value`. Otherwise, if the user has an active notebook
   * cell, this function replaces the contents of the active cell with `value`.
   *
   * Otherwise (if a user does not have a text selection or active cell), this
   * function does nothing.
   */
  replace: (value: string) => unknown;
  /**
   * Whether the replace button should be disabled, i.e. the user does not have
   * a text selection or active cell.
   */
  replaceDisabled: boolean;
  /**
   * Label that should be shown by the replace button using this hook.
   */
  replaceLabel: string;
};

/**
 * Hook that provides a function to either replace a text selection or an active
 * cell. Manages related UI state. Should be used by any button that intends to
 * replace some user selection.
 */
export function useReplace(): UseReplaceReturn {
  const [textSelection, replaceTextSelection] = useSelectionContext();
  const activeCell = useActiveCellContext();

  const replace = (value: string) => {
    if (textSelection) {
      replaceTextSelection({ ...textSelection, text: value });
    } else if (activeCell.exists) {
      activeCell.manager.replace(value);
    }
  };

  const replaceDisabled = !(textSelection || activeCell.exists);

  const numLines = textSelection?.text.split('\n').length || 0;
  const replaceLabel = textSelection
    ? `Replace selection (${numLines} ${numLines === 1 ? 'line' : 'lines'})`
    : activeCell.exists
    ? 'Replace selection (1 active cell)'
    : 'Replace selection (no selection or active cell)';

  return {
    replace,
    replaceDisabled,
    replaceLabel
  };
}
