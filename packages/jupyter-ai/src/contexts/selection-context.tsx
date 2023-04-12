import React, { useCallback, useContext, useEffect, useState } from 'react';
import { Selection, SelectionWatcher } from '../selection-watcher';

const SelectionContext = React.createContext<
  [Selection | null, (value: Selection) => unknown]
>([
  null,
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
  const [selection, setSelection] = useState<Selection | null>(null);

  /**
   * Effect: subscribe to SelectionWatcher
   */
  useEffect(() => {
    selectionWatcher.selectionChanged.connect((sender, newSelection) => {
      setSelection(newSelection);
    });
  }, []);

  const replaceSelection = useCallback(
    (value: Selection) => {
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
