import React, { useEffect, useState } from 'react';
import { Box } from '@mui/system';
import {
  Alert,
  Button,
  MenuItem,
  TextField,
  CircularProgress
} from '@mui/material';

import { Select } from './select';
import { AiService } from '../handler';

enum ChatSettingsState {
  // chat settings is making initial fetches
  Loading,
  // chat settings is ready (happy path)
  Ready,
  // chat settings failed to make initial fetches
  FetchError,
  // chat settings failed to submit the save request
  SubmitError,
  // chat settings successfully submitted the save request
  Success
}

export function ChatSettings() {
  const [state, setState] = useState<ChatSettingsState>(
    ChatSettingsState.Loading
  );
  // error message from initial fetch
  const [fetchEmsg, setFetchEmsg] = useState<string>();

  // state fetched on initial render
  const [config, setConfig] = useState<AiService.GetConfigResponse>();
  const [lmProviders, setLmProviders] =
    useState<AiService.ListProvidersResponse>();
  const [emProviders, setEmProviders] =
    useState<AiService.ListProvidersResponse>();

  // user inputs
  const [inputConfig, setInputConfig] = useState<AiService.Config>({
    model_provider_id: null,
    embeddings_provider_id: null,
    api_keys: {}
  });

  // whether the form is currently saving
  const [saving, setSaving] = useState<boolean>(false);
  // error message from submission
  const [saveEmsg, setSaveEmsg] = useState<string>();

  /**
   * Effect: call APIs on initial render
   */
  useEffect(() => {
    async function getConfig() {
      try {
        const [config, lmProviders, emProviders] = await Promise.all([
          AiService.getConfig(),
          AiService.listLmProviders(),
          AiService.listEmProviders()
        ]);
        setConfig(config);
        setInputConfig(config);
        setLmProviders(lmProviders);
        setEmProviders(emProviders);
        setState(ChatSettingsState.Ready);
      } catch (e) {
        console.error(e);
        if (e instanceof Error) {
          setFetchEmsg(e.message);
        }
        setState(ChatSettingsState.FetchError);
      }
    }
    getConfig();
  }, []);

  /**
   * Effect: re-initialize API keys object whenever the selected LM/EM changes.
   */
  useEffect(() => {
    const selectedLmpId = inputConfig.model_provider_id?.split(':')[0];
    const selectedEmpId = inputConfig.embeddings_provider_id?.split(':')[0];
    const lmp = lmProviders?.providers.find(
      provider => provider.id === selectedLmpId
    );
    const emp = emProviders?.providers.find(
      provider => provider.id === selectedEmpId
    );
    const newApiKeys: Record<string, string> = {};

    if (lmp?.auth_strategy && lmp.auth_strategy.type === 'env') {
      newApiKeys[lmp.auth_strategy.name] =
        config?.api_keys[lmp.auth_strategy.name] || '';
    }
    if (emp?.auth_strategy && emp.auth_strategy.type === 'env') {
      newApiKeys[emp.auth_strategy.name] =
        config?.api_keys[emp.auth_strategy.name] || '';
    }

    setInputConfig(inputConfig => ({
      ...inputConfig,
      api_keys: { ...config?.api_keys, ...newApiKeys }
    }));
  }, [inputConfig.model_provider_id, inputConfig.embeddings_provider_id]);

  const handleSave = async () => {
    const inputConfigCopy: AiService.Config = {
      ...inputConfig,
      api_keys: { ...inputConfig.api_keys }
    };

    // delete any empty api keys
    for (const apiKey in inputConfigCopy.api_keys) {
      if (inputConfigCopy.api_keys[apiKey] === '') {
        delete inputConfigCopy.api_keys[apiKey];
      }
    }

    setSaving(true);
    try {
      await AiService.updateConfig(inputConfigCopy);
    } catch (e) {
      console.error(e);
      if (e instanceof Error) {
        setSaveEmsg(e.message);
      }
      setState(ChatSettingsState.SubmitError);
    }
    setState(ChatSettingsState.Success);
    setSaving(false);
  };

  if (state === ChatSettingsState.Loading) {
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

  if (
    state === ChatSettingsState.FetchError ||
    !lmProviders ||
    !emProviders ||
    !config
  ) {
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
          {fetchEmsg
            ? `An error occurred. Error details:\n\n${fetchEmsg}`
            : 'An unknown error occurred. Check the console for more details.'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        padding: 4,
        boxSizing: 'border-box',
        '& > .MuiAlert-root': { marginBottom: 2 }
      }}
    >
      {state === ChatSettingsState.SubmitError && (
        <Alert severity="error">
          {saveEmsg
            ? `An error occurred. Error details:\n\n${saveEmsg}`
            : 'An unknown error occurred. Check the console for more details.'}
        </Alert>
      )}
      {state === ChatSettingsState.Success && (
        <Alert severity="success">Settings saved successfully.</Alert>
      )}
      <Select
        value={inputConfig.model_provider_id}
        label="Language model"
        onChange={e =>
          setInputConfig(inputConfig => ({
            ...inputConfig,
            model_provider_id: e.target.value
          }))
        }
        MenuProps={{ sx: { maxHeight: '50%', minHeight: 400 } }}
      >
        <MenuItem value="null">None</MenuItem>
        {lmProviders.providers.map(lmp =>
          lmp.models
            .filter(lm => lm !== '*') // TODO: support registry providers
            .map(lm => (
              <MenuItem value={`${lmp.id}:${lm}`}>
                {lmp.name} :: {lm}
              </MenuItem>
            ))
        )}
      </Select>
      <Select
        value={inputConfig.embeddings_provider_id}
        label="Embedding model"
        onChange={e =>
          setInputConfig(inputConfig => ({
            ...inputConfig,
            embeddings_provider_id: e.target.value
          }))
        }
        MenuProps={{ sx: { maxHeight: '50%', minHeight: 400 } }}
      >
        <MenuItem value="null">None</MenuItem>
        {emProviders.providers.map(emp =>
          emp.models
            .filter(em => em !== '*') // TODO: support registry providers
            .map(em => (
              <MenuItem value={`${emp.id}:${em}`}>
                {emp.name} :: {em}
              </MenuItem>
            ))
        )}
      </Select>
      {Object.entries(inputConfig.api_keys).map(
        ([apiKey, apiKeyValue], idx) => (
          <TextField
            key={idx}
            label={apiKey}
            value={apiKeyValue}
            fullWidth
            type="password"
            onChange={e =>
              setInputConfig(inputConfig => ({
                ...inputConfig,
                api_keys: {
                  ...inputConfig.api_keys,
                  [apiKey]: e.target.value
                }
              }))
            }
          />
        )
      )}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button variant="contained" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save changes'}
        </Button>
      </Box>
    </Box>
  );
}
