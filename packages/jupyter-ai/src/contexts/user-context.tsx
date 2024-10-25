import React, { useContext, useEffect, useState } from 'react';
import type { User } from '@jupyterlab/services';
import { PartialJSONObject } from '@lumino/coreutils';

const UserContext = React.createContext<User.IUser | null>(null);

export function useUserContext(): User.IUser | null {
  return useContext(UserContext);
}

type UserContextProviderProps = {
  userManager: User.IManager;
  children: React.ReactNode;
};

export function UserContextProvider({
  userManager,
  children
}: UserContextProviderProps): JSX.Element {
  const [user, setUser] = useState<User.IUser | null>(null);

  useEffect(() => {
    userManager.ready.then(() => {
      setUser({
        identity: userManager.identity!,
        permissions: userManager.permissions as PartialJSONObject
      });
    });
    userManager.userChanged.connect((sender, newUser) => {
      setUser(newUser);
    });
  }, []);

  return <UserContext.Provider value={user}>{children}</UserContext.Provider>;
}
