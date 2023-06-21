import React, { useContext, useEffect, useState } from 'react';
import type { Awareness } from 'y-protocols/awareness';

import { AiService } from '../handler';

const CollaboratorsContext = React.createContext<
  Record<string, AiService.Collaborator>
>({});

/**
 * Returns a dictionary mapping each collaborator's username to their associated
 * Collaborator object.
 */
// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export function useCollaboratorsContext() {
  return useContext(CollaboratorsContext);
}

type GlobalAwarenessStates = Map<
  number,
  { current: string; user: AiService.Collaborator }
>;

type CollaboratorsContextProviderProps = {
  globalAwareness: Awareness | null;
  children: JSX.Element;
};

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export function CollaboratorsContextProvider({
  globalAwareness,
  children
}: CollaboratorsContextProviderProps) {
  const [collaborators, setCollaborators] = useState<
    Record<string, AiService.Collaborator>
  >({});

  /**
   * Effect: listen to changes in global awareness and update collaborators
   * dictionary.
   */
  useEffect(() => {
    function handleChange() {
      const states = (globalAwareness?.getStates() ??
        new Map()) as GlobalAwarenessStates;

      const collaboratorsDict: Record<string, AiService.Collaborator> = {};
      states.forEach(state => {
        collaboratorsDict[state.user.username] = state.user;
      });

      setCollaborators(collaboratorsDict);
    }

    globalAwareness?.on('change', handleChange);
    return () => {
      globalAwareness?.off('change', handleChange);
    };
  }, [globalAwareness]);

  if (!globalAwareness) {
    return children;
  }

  return (
    <CollaboratorsContext.Provider value={collaborators}>
      {children}
    </CollaboratorsContext.Provider>
  );
}
