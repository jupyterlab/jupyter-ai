import React, { useCallback, useContext, useEffect, useState } from 'react';
import { SelectionWatcher } from '../selection-watcher';

const SelectionContext = React.createContext<
  [string, (value: string) => unknown]
>([
  '',
  () => {
    /* noop */
  }
]);

export function useSelectionContext() {
  return useContext(SelectionContext);
}

type SelectionContextProviderProps = {
  selectionWatcher: SelectionWatcher;
  children: React.ReactNode;
};

export function SelectionContextProvider({
  selectionWatcher,
  children
}: SelectionContextProviderProps) {
  const [selection, setSelection] = useState('');

  /**
   * Effect: subscribe to SelectionWatcher
   */
  useEffect(() => {
    selectionWatcher.selectionChanged.connect((sender, newSelection) => {
      setSelection(newSelection);
    });
  }, []);

  const replaceSelection = useCallback(
    (value: string) => {
      selectionWatcher.replaceSelection(value);
    },
    [selectionWatcher]
  );

  return (
    <SelectionContext.Provider value={[selection, replaceSelection]}>
      {children}
    </SelectionContext.Provider>
  );
}
