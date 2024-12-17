import { INotebookTracker } from '@jupyterlab/notebook';
import React, { useContext } from 'react';

/**
 * NotebookTrackerContext is a React context that holds an INotebookTracker instance or null.
 * It is used to provide access to the notebook tracker object throughout the React component tree.
 */
export const NotebookTrackerContext = React.createContext<INotebookTracker | null>(null);

/**
 * useNotebookTrackerContext is a custom hook that provides access to the current value of the NotebookTrackerContext.
 * This hook allows components to easily access the notebook tracker without directly using the context API.
 *
 * @returns The current value of the NotebookTrackerContext, which is either an INotebookTracker instance or null.
 */
export const useNotebookTrackerContext = () => {
    const tracker =  useContext(NotebookTrackerContext);
    return tracker;
}
