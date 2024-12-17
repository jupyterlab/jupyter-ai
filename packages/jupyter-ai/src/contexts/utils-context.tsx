import React, { useContext } from 'react';

/**
 * UtilsContext is a React context that holds an object with an optional goBackToNotebook function.
 * It is used to provide utility functions throughout the React component tree.
 */
export const UtilsContext = React.createContext<{
    goBackToNotebook?: () => void;
}>({});

/**
 * useUtilsContext is a custom hook that provides access to the current value of the UtilsContext.
 * This hook allows components to easily access the utility functions without directly using the context API.
 *
 * @returns The current value of the UtilsContext, which is an object that may contain a goBackToNotebook function.
 */
export const useUtilsContext = () => {
    const utils = useContext(UtilsContext);
    return utils;
}
