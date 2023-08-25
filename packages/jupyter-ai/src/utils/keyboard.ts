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
