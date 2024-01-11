import React, { useState, useEffect } from 'react';

import { Theme, ThemeProvider, createTheme } from '@mui/material/styles';
import { getJupyterLabTheme, getThemeManager } from '../theme-provider';

export function JlThemeProvider(props: {
  children: React.ReactNode;
}): JSX.Element {
  const [theme, setTheme] = useState<Theme>(createTheme());

  useEffect(() => {
    async function setJlTheme() {
      setTheme(await getJupyterLabTheme());
    }
    setJlTheme();

    const manager = getThemeManager();
    if (manager) {
      manager.themeChanged.connect(setJlTheme);
    }
  }, []);

  return <ThemeProvider theme={theme}>{props.children}</ThemeProvider>;
}
