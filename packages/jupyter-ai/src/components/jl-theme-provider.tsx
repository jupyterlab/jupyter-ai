import React, { useState, useEffect } from 'react';
import type { IThemeManager } from '@jupyterlab/apputils';
import { Theme, ThemeProvider, createTheme } from '@mui/material/styles';

import { getJupyterLabTheme } from '../theme-provider';

export function JlThemeProvider(props: {
  themeManager: IThemeManager | null;
  children: React.ReactNode;
}): JSX.Element {
  const [theme, setTheme] = useState<Theme>(createTheme());

  useEffect(() => {
    async function setJlTheme() {
      setTheme(await getJupyterLabTheme());
    }

    setJlTheme();
    props.themeManager?.themeChanged.connect(setJlTheme);
  }, []);

  return <ThemeProvider theme={theme}>{props.children}</ThemeProvider>;
}
