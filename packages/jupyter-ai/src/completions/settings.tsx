import { ReactWidget } from '@jupyterlab/ui-components';
import React, { useState } from 'react';

import { Box } from '@mui/system';
import { Alert, Button, CircularProgress } from '@mui/material';

import { AiService } from '../handler';
import {
  ServerInfoState,
  useServerInfo
} from '../components/settings/use-server-info';
import { ModelSettings, IModelSettings } from '../components/model-settings';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { minifyUpdate } from '../components/settings/minify';
import { useStackingAlert } from '../components/mui-extras/stacking-alert';

type CompleterSettingsProps = {
  rmRegistry: IRenderMimeRegistry;
  isProviderEnabled: () => boolean;
  openInlineCompleterSettings: () => void;
};

/**
 * Component that returns the settings view.
 */
export function CompleterSettings(props: CompleterSettingsProps): JSX.Element {
  // state fetched on initial render
  const server = useServerInfo();

  // initialize alert helper
  const alert = useStackingAlert();

  // whether the form is currently saving
  const [saving, setSaving] = useState(false);

  // provider/model settings
  const [modelSettings, setModelSettings] = useState<IModelSettings>({
    fields: {},
    apiKeys: {},
    emGlobalId: null,
    lmGlobalId: null
  });

  const handleSave = async () => {
    // compress fields with JSON values
    if (server.state !== ServerInfoState.Ready) {
      return;
    }

    const { fields, lmGlobalId, emGlobalId, apiKeys } = modelSettings;

    for (const fieldKey in fields) {
      const fieldVal = fields[fieldKey];
      if (typeof fieldVal !== 'string' || !fieldVal.trim().startsWith('{')) {
        continue;
      }

      try {
        const parsedFieldVal = JSON.parse(fieldVal);
        const compressedFieldVal = JSON.stringify(parsedFieldVal);
        fields[fieldKey] = compressedFieldVal;
      } catch (e) {
        continue;
      }
    }

    let updateRequest: AiService.UpdateConfigRequest = {
      completions_model_provider_id: lmGlobalId,
      completions_embeddings_provider_id: emGlobalId,
      api_keys: apiKeys,
      ...(lmGlobalId && {
        completions_fields: {
          [lmGlobalId]: fields
        }
      })
    };
    updateRequest = minifyUpdate(server.config, updateRequest);
    updateRequest.last_read = server.config.last_read;

    setSaving(true);
    try {
      await AiService.updateConfig(updateRequest);
    } catch (e) {
      console.error(e);
      const msg =
        e instanceof Error || typeof e === 'string'
          ? e.toString()
          : 'An unknown error occurred. Check the console for more details.';
      alert.show('error', msg);
      return;
    } finally {
      setSaving(false);
    }
    await server.refetchAll();
    alert.show('success', 'Settings saved successfully.');
  };

  if (server.state === ServerInfoState.Loading) {
    return (
      <Box
        sx={{
          width: '100%',
          height: '100%',
          boxSizing: 'border-box',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-around'
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (server.state === ServerInfoState.Error) {
    return (
      <Box
        sx={{
          width: '100%',
          height: '100%',
          padding: 4,
          boxSizing: 'border-box'
        }}
      >
        <Alert severity="error">
          {server.error ||
            'An unknown error occurred. Check the console for more details.'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        padding: '0 12px 12px',
        boxSizing: 'border-box',
        '& .MuiAlert-root': {
          marginTop: 2
        },
        overflowY: 'auto'
      }}
    >
      {props.isProviderEnabled() ? null : (
        <Alert severity="warning">
          The jupyter-ai inline completion provider is not enabled in the Inline
          Completer settings.
          <Button
            variant="contained"
            onClick={props.openInlineCompleterSettings}
          >
            Open Inline Completer Settings
          </Button>
        </Alert>
      )}

      <ModelSettings
        label="Inline Completer language model"
        rmRegistry={props.rmRegistry}
        onChange={setModelSettings}
        modelKind="completions"
      />

      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button variant="contained" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save changes'}
        </Button>
      </Box>
      {alert.jsx}
    </Box>
  );
}

export class ModelSettingsWidget extends ReactWidget {
  constructor(protected options: CompleterSettingsProps) {
    super();
  }
  render(): JSX.Element {
    return <CompleterSettings {...this.options} />;
  }
}
