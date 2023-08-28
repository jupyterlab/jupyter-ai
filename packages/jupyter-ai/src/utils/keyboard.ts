/**
 * Parses a keyboard event to produce a human-readable shortcut string.
 *
 * Given a KeyboardEvent, this function generates a string representation of the key combination,
 * e.g., "Ctrl + Shift + A".
 *
 * @param {React.KeyboardEvent<HTMLInputElement> | KeyboardEvent} event - The keyboard event to parse.
 * @returns {string} - The string representation of the key combination.
 */
export const parseKeyboardEventToShortcut = (
  event: React.KeyboardEvent<HTMLInputElement> | KeyboardEvent
): string => {
  const keyCombo: string[] = [];
  if (event.ctrlKey) {
    keyCombo.push('Ctrl');
  }
  if (event.altKey) {
    keyCombo.push('Alt');
  }
  if (event.shiftKey) {
    keyCombo.push('Shift');
  }
  if (event.metaKey) {
    keyCombo.push('Meta');
  }
  if (['Shift', 'Alt', 'Control', 'Meta'].indexOf(event.key) === -1) {
    keyCombo.push(event.code);
  }

  return keyCombo.join(' + ');
};
