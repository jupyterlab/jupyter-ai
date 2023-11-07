import React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';

import { chatIcon } from '../icons';
import { Alert, Box, Button } from '@mui/material';
import { JlThemeProvider } from '../components/jl-theme-provider';

export function buildErrorWidget(
  deleteConfig: () => Promise<void>
): ReactWidget {
  const ErrorWidget = ReactWidget.create(
    <JlThemeProvider>
      <Box
        sx={{
          width: '100%',
          height: '100%',
          boxSizing: 'border-box',
          background: 'var(--jp-layout-color0)',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        <Box sx={{ padding: 4 }}>
          <Alert severity="error">
            There seems to be a problem with the Chat backend, please look at
            the JupyterLab server logs or contact your administrator to correct
            this problem. Deleting the config file
            `$JUPYTER_DATA_DIR/jupyter_ai/config.json` and then restarting
            `jupyter lab` may fix the issue if it is a result of the config
            changes.
          </Alert>
          <Box sx={{ marginTop: 2 }}>
            <Button variant="contained" onClick={deleteConfig}>
              Delete Config File
            </Button>
          </Box>
        </Box>
      </Box>
    </JlThemeProvider>
  );
  ErrorWidget.id = 'jupyter-ai::chat';
  ErrorWidget.title.icon = chatIcon;
  ErrorWidget.title.caption = 'Jupyter AI Chat'; // TODO: i18n

  return ErrorWidget;
}
