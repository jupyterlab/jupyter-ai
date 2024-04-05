import React, { useEffect, useState } from 'react';

import { Box } from '@mui/system';
import {
  Alert,
  Button,
  FormControl,
  FormControlLabel,
  FormLabel,
  Radio,
  RadioGroup,
  CircularProgress
} from '@mui/material';

import { AiService } from '../handler';
import { ServerInfoState, useServerInfo } from './settings/use-server-info';
import { ModelSettings, IModelSettings } from './model-settings';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { minifyUpdate } from './settings/minify';
import { useStackingAlert } from './mui-extras/stacking-alert';

type ChatSettingsProps = {
  rmRegistry: IRenderMimeRegistry;
};

/**
 * Component that returns the settings view in the chat panel.
 */
export function ChatSettings(props: ChatSettingsProps): JSX.Element {
  // state fetched on initial render
  const server = useServerInfo();

  // initialize alert helper
  const alert = useStackingAlert();

  // user inputs
  const [sendWse, setSendWse] = useState<boolean>(false);

  // whether the form is currently saving
  const [saving, setSaving] = useState(false);

  // provider/model settings
  const [modelSettings, setModelSettings] = useState<IModelSettings>({
    fields: {},
    apiKeys: {},
    emGlobalId: null,
    lmGlobalId: null
  });

  /**
   * Effect: initialize inputs after fetching server info.
   */
  useEffect(() => {
    if (server.state !== ServerInfoState.Ready) {
      return;
    }
    setSendWse(server.config.send_with_shift_enter);
  }, [server]);

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
      model_provider_id: lmGlobalId,
      embeddings_provider_id: emGlobalId,
      api_keys: apiKeys,
      ...(lmGlobalId && {
        fields: {
          [lmGlobalId]: fields
        }
      }),
      send_with_shift_enter: sendWse
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
      <ModelSettings
        label="Chat language model"
        rmRegistry={props.rmRegistry}
        onChange={setModelSettings}
        modelKind="chat"
      />

      {/* Input */}
      <h2 className="jp-ai-ChatSettings-header">Input</h2>
      <FormControl>
        <FormLabel id="send-radio-buttons-group-label">
          When writing a message, press <kbd>Enter</kbd> to:
        </FormLabel>
        <RadioGroup
          aria-labelledby="send-radio-buttons-group-label"
          value={sendWse ? 'newline' : 'send'}
          name="send-radio-buttons-group"
          onChange={e => {
            setSendWse(e.target.value === 'newline');
          }}
        >
          <FormControlLabel
            value="send"
            control={<Radio />}
            label="Send the message"
          />
          <FormControlLabel
            value="newline"
            control={<Radio />}
            label={
              <>
                Start a new line (use <kbd>Shift</kbd>+<kbd>Enter</kbd> to send)
              </>
            }
          />
        </RadioGroup>
      </FormControl>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button variant="contained" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save changes'}
        </Button>
      </Box>
      {alert.jsx}
    </Box>
  );
}
