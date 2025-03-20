import React, { useEffect, useState, useMemo } from 'react';

import { Box } from '@mui/system';
import {
  Alert,
  Button,
  IconButton,
  FormControl,
  FormControlLabel,
  FormLabel,
  MenuItem,
  Radio,
  RadioGroup,
  TextField,
  Tooltip,
  CircularProgress
} from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

import { Select } from './select';
import { AiService } from '../handler';
import { ModelFields } from './settings/model-fields';
import { ServerInfoState, useServerInfo } from './settings/use-server-info';
import { ExistingApiKeys } from './settings/existing-api-keys';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { minifyUpdate } from './settings/minify';
import { useStackingAlert } from './mui-extras/stacking-alert';
import { RendermimeMarkdown } from './settings/rendermime-markdown';
import { IJaiCompletionProvider } from '../tokens';
import { getProviderId, getModelLocalId } from '../utils';

type ChatSettingsProps = {
  rmRegistry: IRenderMimeRegistry;
  completionProvider: IJaiCompletionProvider | null;
  openInlineCompleterSettings: () => void;
  // The temporary input options,  should be removed when jupyterlab chat is
  // the only chat.
  inputOptions?: boolean;
};

/**
 * Component that returns the settings view in the chat panel.
 */
export function ChatSettings(props: ChatSettingsProps): JSX.Element {
  // state fetched on initial render
  const server = useServerInfo();

  // initialize alert helper
  const alert = useStackingAlert();
  const apiKeysAlert = useStackingAlert();

  // user inputs
  const [lmProvider, setLmProvider] =
    useState<AiService.ListProvidersEntry | null>(null);
  const [emProvider, setEmProvider] =
    useState<AiService.ListProvidersEntry | null>(null);
  const [clmProvider, setClmProvider] =
    useState<AiService.ListProvidersEntry | null>(null);
  const [showLmLocalId, setShowLmLocalId] = useState<boolean>(false);
  const [showEmLocalId, setShowEmLocalId] = useState<boolean>(false);
  const [showClmLocalId, setShowClmLocalId] = useState<boolean>(false);
  const [chatHelpMarkdown, setChatHelpMarkdown] = useState<string | null>(null);
  const [embeddingHelpMarkdown, setEmbeddingHelpMarkdown] = useState<
    string | null
  >(null);
  const [completionHelpMarkdown, setCompletionHelpMarkdown] = useState<
    string | null
  >(null);
  const [lmLocalId, setLmLocalId] = useState<string>('');
  const [emLocalId, setEmLocalId] = useState<string>('');
  const [clmLocalId, setClmLocalId] = useState<string>('');

  const lmGlobalId = useMemo<string | null>(() => {
    if (!lmProvider) {
      return null;
    }

    return lmProvider.id + ':' + lmLocalId;
  }, [lmProvider, lmLocalId]);

  const emGlobalId = useMemo<string | null>(() => {
    if (!emProvider) {
      return null;
    }

    return emProvider.id + ':' + emLocalId;
  }, [emProvider, emLocalId]);

  const clmGlobalId = useMemo<string | null>(() => {
    if (!clmProvider) {
      return null;
    }

    return clmProvider.id + ':' + clmLocalId;
  }, [clmProvider, clmLocalId]);

  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [sendWse, setSendWse] = useState<boolean>(false);
  const [lmFields, setLmFields] = useState<Record<string, any>>({});
  const [emFields, setEmFields] = useState<Record<string, any>>({});
  const [clmFields, setClmFields] = useState<Record<string, any>>({});
  const [isCompleterEnabled, setIsCompleterEnabled] = useState(
    props.completionProvider && props.completionProvider.isEnabled()
  );

  useEffect(() => {
    const refreshCompleterState = () => {
      setIsCompleterEnabled(
        props.completionProvider && props.completionProvider.isEnabled()
      );
    };
    props.completionProvider?.settingsChanged.connect(refreshCompleterState);
    return () => {
      props.completionProvider?.settingsChanged.disconnect(
        refreshCompleterState
      );
    };
  }, [props.completionProvider]);

  // whether the form is currently saving
  const [saving, setSaving] = useState(false);

  /**
   * Effect: initialize inputs after fetching server info.
   */
  useEffect(() => {
    if (server.state !== ServerInfoState.Ready) {
      return;
    }

    setLmLocalId(server.chat.lmLocalId);
    setEmLocalId(server.chat.emLocalId);
    setClmLocalId(server.completions.lmLocalId);
    setSendWse(server.config.send_with_shift_enter);
    setChatHelpMarkdown(server.chat.lmProvider?.help ?? null);
    setEmbeddingHelpMarkdown(server.chat.emProvider?.help ?? null);
    setCompletionHelpMarkdown(server.completions.lmProvider?.help ?? null);
    if (server.chat.lmProvider?.registry) {
      setShowLmLocalId(true);
    }
    if (server.chat.emProvider?.registry) {
      setShowEmLocalId(true);
    }
    if (server.completions.lmProvider?.registry) {
      setShowClmLocalId(true);
    }
    setLmProvider(server.chat.lmProvider);
    setClmProvider(server.completions.lmProvider);
    setEmProvider(server.chat.emProvider);
  }, [server]);

  /**
   * Effect: re-initialize apiKeys object whenever the selected LM/EM changes.
   * Properties with a value of '' indicate necessary user input.
   */
  useEffect(() => {
    if (server.state !== ServerInfoState.Ready) {
      return;
    }

    const newApiKeys: Record<string, string> = {};
    const lmAuth = lmProvider?.auth_strategy;
    const emAuth = emProvider?.auth_strategy;
    if (
      lmAuth?.type === 'env' &&
      !server.config.api_keys.includes(lmAuth.name)
    ) {
      newApiKeys[lmAuth.name] = '';
    }
    if (lmAuth?.type === 'multienv') {
      lmAuth.names.forEach(apiKey => {
        if (!server.config.api_keys.includes(apiKey)) {
          newApiKeys[apiKey] = '';
        }
      });
    }

    if (
      emAuth?.type === 'env' &&
      !server.config.api_keys.includes(emAuth.name)
    ) {
      newApiKeys[emAuth.name] = '';
    }
    if (emAuth?.type === 'multienv') {
      emAuth.names.forEach(apiKey => {
        if (!server.config.api_keys.includes(apiKey)) {
          newApiKeys[apiKey] = '';
        }
      });
    }

    setApiKeys(newApiKeys);
  }, [lmProvider, emProvider, server]);

  /**
   * Effect: re-initialize fields object whenever the selected LM changes.
   */
  useEffect(() => {
    if (server.state !== ServerInfoState.Ready || !lmGlobalId) {
      return;
    }

    const currFields: Record<string, any> =
      server.config.fields?.[lmGlobalId] ?? {};
    setLmFields(currFields);

    if (!emGlobalId) {
      return;
    }

    const initEmbeddingModelFields: Record<string, any> =
      server.config.embeddings_fields?.[emGlobalId] ?? {};
    setEmFields(initEmbeddingModelFields);

    if (!clmGlobalId) {
      return;
    }

    const initCompleterModelFields: Record<string, any> =
      server.config.completions_fields?.[clmGlobalId] ?? {};
    setClmFields(initCompleterModelFields);
  }, [server, lmGlobalId, emGlobalId, clmGlobalId]);

  const handleSave = async () => {
    // compress fields with JSON values
    if (server.state !== ServerInfoState.Ready) {
      return;
    }

    for (const fieldKey in lmFields) {
      const fieldVal = lmFields[fieldKey];
      if (typeof fieldVal !== 'string' || !fieldVal.trim().startsWith('{')) {
        continue;
      }

      try {
        const parsedFieldVal = JSON.parse(fieldVal);
        const compressedFieldVal = JSON.stringify(parsedFieldVal);
        lmFields[fieldKey] = compressedFieldVal;
      } catch (e) {
        continue;
      }
    }

    for (const fieldKey in emFields) {
      const fieldVal = emFields[fieldKey];
      if (typeof fieldVal !== 'string' || !fieldVal.trim().startsWith('{')) {
        continue;
      }

      try {
        const parsedFieldVal = JSON.parse(fieldVal);
        const compressedFieldVal = JSON.stringify(parsedFieldVal);
        emFields[fieldKey] = compressedFieldVal;
      } catch (e) {
        continue;
      }
    }

    for (const fieldKey in clmFields) {
      const fieldVal = clmFields[fieldKey];
      if (typeof fieldVal !== 'string' || !fieldVal.trim().startsWith('{')) {
        continue;
      }

      try {
        const parsedFieldVal = JSON.parse(fieldVal);
        const compressedFieldVal = JSON.stringify(parsedFieldVal);
        clmFields[fieldKey] = compressedFieldVal;
      } catch (e) {
        continue;
      }
    }

    let updateRequest: AiService.UpdateConfigRequest = {
      model_provider_id: lmGlobalId,
      embeddings_provider_id: emGlobalId,
      api_keys: apiKeys,
      fields: lmGlobalId ? { [lmGlobalId]: lmFields } : {},
      completions_fields: clmGlobalId ? { [clmGlobalId]: clmFields } : {},
      embeddings_fields: emGlobalId ? { [emGlobalId]: emFields } : {},
      completions_model_provider_id: clmGlobalId,
      send_with_shift_enter: sendWse
    };
    updateRequest = minifyUpdate(server.config, updateRequest);
    updateRequest.last_read = server.config.last_read;

    setSaving(true);
    try {
      await apiKeysAlert.clear();
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
      {/* Chat language model section */}
      <h2
        className="jp-ai-ChatSettings-header"
        title="The language model used in the chat panel"
      >
        Language model
      </h2>

      {server.lmProviders.providers
        .map(lmp => lmp.chat_models.length)
        .reduce((partialSum, num) => partialSum + num, 0) > 0 ? (
        <Box>
          <Select
            value={lmProvider?.registry ? lmProvider.id + ':*' : lmGlobalId}
            label="Completion model"
            onChange={e => {
              const lmGid = e.target.value === 'null' ? null : e.target.value;
              if (lmGid === null) {
                setLmProvider(null);
                return;
              }

              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              const nextLmProvider = getProvider(lmGid, server.lmProviders)!;
              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              const nextLmLocalId = getModelLocalId(lmGid)!;

              setLmProvider(nextLmProvider);
              setChatHelpMarkdown(nextLmProvider?.help ?? null);
              if (nextLmProvider.registry) {
                setLmLocalId('');
                setShowLmLocalId(true);
              } else {
                setLmLocalId(nextLmLocalId);
                setShowLmLocalId(false);
              }
            }}
            MenuProps={{ sx: { maxHeight: '50%', minHeight: 400 } }}
          >
            <MenuItem value="null">None</MenuItem>
            {server.lmProviders.providers.map(lmp =>
              lmp.models
                .filter(lm => lmp.chat_models.includes(lm))
                .map(lm => (
                  <MenuItem value={`${lmp.id}:${lm}`}>
                    {lmp.name} :: {lm}
                  </MenuItem>
                ))
            )}
          </Select>
          {showLmLocalId && (
            <TextField
              label={lmProvider?.model_id_label || 'Local model ID'}
              value={lmLocalId}
              onChange={e => setLmLocalId(e.target.value)}
              fullWidth
            />
          )}
          {chatHelpMarkdown && (
            <RendermimeMarkdown
              rmRegistry={props.rmRegistry}
              markdownStr={chatHelpMarkdown}
            />
          )}
          {lmGlobalId && (
            <ModelFields
              fields={lmProvider?.fields}
              values={lmFields}
              onChange={setLmFields}
            />
          )}
        </Box>
      ) : (
        <p>No language models available.</p>
      )}

      {/* Embedding model section */}
      <h2 className="jp-ai-ChatSettings-header">Embedding model</h2>
      {server.emProviders.providers.length > 0 ? (
        <Box>
          <Select
            value={emProvider?.registry ? emProvider.id + ':*' : emGlobalId}
            label="Embedding model"
            onChange={e => {
              const emGid = e.target.value === 'null' ? null : e.target.value;
              if (emGid === null) {
                setEmProvider(null);
                return;
              }

              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              const nextEmProvider = getProvider(emGid, server.emProviders)!;
              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              const nextEmLocalId = getModelLocalId(emGid)!;

              setEmProvider(nextEmProvider);
              setEmbeddingHelpMarkdown(nextEmProvider?.help ?? null);
              if (nextEmProvider.registry) {
                setEmLocalId('');
                setShowEmLocalId(true);
              } else {
                setEmLocalId(nextEmLocalId);
                setShowEmLocalId(false);
              }
            }}
            MenuProps={{ sx: { maxHeight: '50%', minHeight: 400 } }}
          >
            <MenuItem value="null">None</MenuItem>
            {server.emProviders.providers.map(emp =>
              emp.models.map(em => (
                <MenuItem value={`${emp.id}:${em}`}>
                  {emp.name} :: {em}
                </MenuItem>
              ))
            )}
          </Select>
          {showEmLocalId && (
            <TextField
              label={emProvider?.model_id_label || 'Local model ID'}
              value={emLocalId}
              onChange={e => setEmLocalId(e.target.value)}
              fullWidth
            />
          )}
          {embeddingHelpMarkdown && (
            <RendermimeMarkdown
              rmRegistry={props.rmRegistry}
              markdownStr={embeddingHelpMarkdown}
            />
          )}
          {emGlobalId && (
            <ModelFields
              fields={emProvider?.fields}
              values={emFields}
              onChange={setEmFields}
            />
          )}
        </Box>
      ) : (
        <p>No embedding models available.</p>
      )}

      {/* Completer language model section */}
      <h2 className="jp-ai-ChatSettings-header">
        Inline completions model
        <CompleterSettingsButton
          provider={props.completionProvider}
          openSettings={props.openInlineCompleterSettings}
          isCompleterEnabled={isCompleterEnabled}
          selection={clmProvider}
        />
      </h2>
      {server.lmProviders.providers
        .map(lmp => lmp.completion_models.length)
        .reduce((partialSum, num) => partialSum + num, 0) > 0 ? (
        <Box>
          <Select
            value={clmProvider?.registry ? clmProvider.id + ':*' : clmGlobalId}
            label="Inline completion model"
            disabled={!isCompleterEnabled}
            onChange={e => {
              const clmGid = e.target.value === 'null' ? null : e.target.value;
              if (clmGid === null) {
                setClmProvider(null);
                return;
              }

              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              const nextClmProvider = getProvider(clmGid, server.lmProviders)!;
              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              const nextClmLocalId = getModelLocalId(clmGid)!;

              setClmProvider(nextClmProvider);
              setCompletionHelpMarkdown(nextClmProvider?.help ?? null);
              if (nextClmProvider.registry) {
                setClmLocalId('');
                setShowClmLocalId(true);
              } else {
                setClmLocalId(nextClmLocalId);
                setShowClmLocalId(false);
              }
            }}
            MenuProps={{ sx: { maxHeight: '50%', minHeight: 400 } }}
          >
            <MenuItem value="null">None</MenuItem>
            {server.lmProviders.providers.map(lmp =>
              lmp.models
                .filter(lm => lmp.completion_models.includes(lm))
                .map(lm => (
                  <MenuItem value={`${lmp.id}:${lm}`}>
                    {lmp.name} :: {lm}
                  </MenuItem>
                ))
            )}
          </Select>
          {showClmLocalId && (
            <TextField
              label={clmProvider?.model_id_label || 'Local model ID'}
              value={clmLocalId}
              onChange={e => setClmLocalId(e.target.value)}
              fullWidth
            />
          )}
          {completionHelpMarkdown && (
            <RendermimeMarkdown
              rmRegistry={props.rmRegistry}
              markdownStr={completionHelpMarkdown}
            />
          )}
          {clmGlobalId && (
            <ModelFields
              fields={clmProvider?.fields}
              values={clmFields}
              onChange={setClmFields}
            />
          )}
        </Box>
      ) : (
        <p>No Inline Completion models.</p>
      )}

      {/* API Keys section */}
      <h2 className="jp-ai-ChatSettings-header">API Keys</h2>

      {Object.entries(apiKeys).length === 0 &&
      server.config.api_keys.length === 0 ? (
        <p>No API keys are required by the selected models.</p>
      ) : null}

      {/* API key inputs for newly-used providers */}
      {Object.entries(apiKeys).map(([apiKeyName, apiKeyValue], idx) => (
        <TextField
          key={idx}
          label={apiKeyName}
          value={apiKeyValue}
          fullWidth
          type="password"
          onChange={e =>
            setApiKeys(apiKeys => ({
              ...apiKeys,
              [apiKeyName]: e.target.value
            }))
          }
        />
      ))}
      {/* Pre-existing API keys */}
      <ExistingApiKeys
        alert={apiKeysAlert}
        apiKeys={server.config.api_keys}
        onSuccess={server.refetchApiKeys}
      />

      {/* Input - to remove when jupyterlab chat is the only chat */}
      {(props.inputOptions ?? true) && (
        <>
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
                    Start a new line (use <kbd>Shift</kbd>+<kbd>Enter</kbd> to
                    send)
                  </>
                }
              />
            </RadioGroup>
          </FormControl>
        </>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button variant="contained" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save changes'}
        </Button>
      </Box>
      {alert.jsx}
    </Box>
  );
}

function CompleterSettingsButton(props: {
  selection: AiService.ListProvidersEntry | null;
  provider: IJaiCompletionProvider | null;
  isCompleterEnabled: boolean | null;
  openSettings: () => void;
}): JSX.Element {
  if (props.selection && !props.isCompleterEnabled) {
    return (
      <Tooltip
        title={
          'A completer model is selected, but ' +
          (props.provider === null
            ? 'the completion provider plugin is not available.'
            : 'the inline completion provider is not enabled in the settings: click to open settings.')
        }
      >
        <IconButton onClick={props.openSettings}>
          <WarningAmberIcon />
        </IconButton>
      </Tooltip>
    );
  }
  return (
    <Tooltip title="Completer settings">
      <IconButton onClick={props.openSettings}>
        <SettingsIcon />
      </IconButton>
    </Tooltip>
  );
}

function getProvider(
  globalModelId: string,
  providers: AiService.ListProvidersResponse
): AiService.ListProvidersEntry | null {
  const providerId = getProviderId(globalModelId);
  const provider = providers.providers.find(p => p.id === providerId);
  return provider ?? null;
}
