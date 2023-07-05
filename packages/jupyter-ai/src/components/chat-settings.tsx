import React, { useEffect, useState, useMemo } from 'react';
import { Box } from '@mui/system';
import {
  Alert,
  Button,
  FormControl,
  FormControlLabel,
  FormLabel,
  MenuItem,
  Radio,
  RadioGroup,
  TextField,
  CircularProgress
} from '@mui/material';

import { Select } from './select';
import { AiService } from '../handler';
import { ModelFields } from './settings/model-fields';

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

function getProviderId(globalModelId: string | null) {
  if (!globalModelId) {
    return null;
  }

  return globalModelId.split(':')[0];
}

function getLocalModelId(globalModelId: string | null) {
  if (!globalModelId) {
    return null;
  }

  const components = globalModelId.split(':');
  return components[components.length - 1];
}

function getProvider(
  globalModelId: string | null,
  providers: AiService.ListProvidersResponse
) {
  const providerId = getProviderId(globalModelId);
  const provider = providers.providers.find(p => p.id === providerId);
  return provider;
}

function fromRegistryProvider(
  globalModelId: string | null,
  providers: AiService.ListProvidersResponse
) {
  return getProvider(globalModelId, providers)?.registry ?? false;
}

/**
 * Component that returns the settings view in the chat panel.
 *
 * Implementation notes:
 * - `config` is the configuration last fetched from the backend. `inputConfig`
 * is the editable copy of that object that stores all user input state.
 *
 * - `inputConfig.model_provider_id` reflects the global model ID only if the
 * provider is not a registry provider. Otherwise, it is set to
 * `<provider-id>:*`.
 */
export function ChatSettings(): JSX.Element {
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
    api_keys: {},
    send_with_shift_enter: null,
    fields: {}
  });

  // whether the form is currently saving
  const [saving, setSaving] = useState<boolean>(false);
  // error message from submission
  const [saveEmsg, setSaveEmsg] = useState<string>();

  // whether to show the language model's local model ID input
  const [showLmLocalId, setShowLmLocalId] = useState<boolean>(false);
  const [lmLocalId, setLmLocalId] = useState<string>('*');

  // provider of the currently selected language model
  const lmProvider = useMemo(() => {
    if (!inputConfig.model_provider_id || !lmProviders) {
      return;
    }

    return getProvider(inputConfig.model_provider_id, lmProviders);
  }, [inputConfig.model_provider_id, lmProviders]);

  // global model ID of the currently selected language model
  const lmGlobalId = useMemo(() => {
    if (!inputConfig.model_provider_id || !lmProvider) {
      return null;
    }

    return lmProvider?.registry
      ? `${lmProvider.id}:${lmLocalId}`
      : inputConfig.model_provider_id;
  }, [inputConfig.model_provider_id, lmProvider, lmProviders, lmLocalId]);

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
        setLmProviders(lmProviders);
        setEmProviders(emProviders);

        // if a model from a registry provider was previously selected, store
        // the local model ID in a separate text field.
        if (fromRegistryProvider(config.model_provider_id, lmProviders)) {
          setShowLmLocalId(true);
          const lmPid = getProviderId(config.model_provider_id);
          setLmLocalId(getLocalModelId(config.model_provider_id) as string);
          setInputConfig({
            ...config,
            model_provider_id: `${lmPid}:*`
          });
        } else {
          setInputConfig(config);
        }

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
    const selectedLmpId = getProviderId(inputConfig.model_provider_id);
    const selectedEmpId = getProviderId(inputConfig.embeddings_provider_id);
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
      model_provider_id: lmGlobalId,
      api_keys: { ...inputConfig.api_keys },
      send_with_shift_enter: inputConfig.send_with_shift_enter ?? true
    };

    // delete any empty api keys
    for (const apiKey in inputConfigCopy.api_keys) {
      if (inputConfigCopy.api_keys[apiKey] === '') {
        delete inputConfigCopy.api_keys[apiKey];
      }
    }

    // compress fields with JSON values
    for (const gmid in inputConfigCopy.fields) {
      for (const fieldKey in inputConfigCopy.fields[gmid]) {
        const fieldVal = inputConfigCopy.fields[gmid][fieldKey];
        if (typeof fieldVal !== 'string') {
          continue;
        }

        try {
          const parsedFieldVal = JSON.parse(fieldVal);
          const compressedFieldVal = JSON.stringify(parsedFieldVal);
          inputConfigCopy.fields[gmid][fieldKey] = compressedFieldVal;
        } catch (e) {
          continue;
        }
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
        '& > .MuiAlert-root': { marginBottom: 2 },
        overflowY: 'auto'
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

      {/* Language model section */}
      <h2 className="jp-ai-ChatSettings-header">Language model</h2>
      <Select
        value={inputConfig.model_provider_id}
        label="Language model"
        onChange={e => {
          setInputConfig(inputConfig => ({
            ...inputConfig,
            model_provider_id: e.target.value
          }));

          // if model is from a registry provider, show an input for the local
          // model ID
          const nextLmProvider = getProvider(e.target.value, lmProviders);
          if (nextLmProvider?.registry) {
            setShowLmLocalId(true);
            setLmLocalId('*');
          } else {
            setShowLmLocalId(false);
          }
        }}
        MenuProps={{ sx: { maxHeight: '50%', minHeight: 400 } }}
      >
        <MenuItem value="null">None</MenuItem>
        {lmProviders.providers.map(lmp =>
          lmp.models.map(lm => (
            <MenuItem value={`${lmp.id}:${lm}`}>
              {lmp.name} :: {lm}
            </MenuItem>
          ))
        )}
      </Select>
      {showLmLocalId && (
        <TextField
          label="Local model ID"
          value={lmLocalId}
          onChange={e => setLmLocalId(e.target.value)}
          fullWidth
        />
      )}
      {lmGlobalId && (
        <ModelFields
          gmid={lmGlobalId}
          config={inputConfig}
          setConfig={setInputConfig}
          fields={lmProvider?.fields}
        />
      )}

      {/* Embedding model section */}
      <h2 className="jp-ai-ChatSettings-header">Embedding model</h2>
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

      {/* API Keys section */}
      <h2 className="jp-ai-ChatSettings-header">API Keys</h2>
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

      {/* Input */}
      <h2 className="jp-ai-ChatSettings-header">Input</h2>
      <FormControl>
        <FormLabel id="send-radio-buttons-group-label">
          When writing a message, press <kbd>Enter</kbd> to:
        </FormLabel>
        <RadioGroup
          aria-labelledby="send-radio-buttons-group-label"
          value={
            inputConfig.send_with_shift_enter ?? false ? 'newline' : 'send'
          }
          name="send-radio-buttons-group"
          onChange={e =>
            setInputConfig(inputConfig => {
              return {
                ...inputConfig,
                send_with_shift_enter:
                  (e.target as HTMLInputElement).value === 'newline'
              };
            })
          }
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
    </Box>
  );
}
