import React, { useEffect, useState, useMemo } from 'react';

import { Box } from '@mui/system';
import { Alert, MenuItem, TextField, CircularProgress } from '@mui/material';

import { Select } from './select';
import { AiService } from '../handler';
import { ModelFields } from './settings/model-fields';
import { ServerInfoState, useServerInfo } from './settings/use-server-info';
import { ExistingApiKeys } from './settings/existing-api-keys';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { useStackingAlert } from './mui-extras/stacking-alert';
import { RendermimeMarkdown } from './rendermime-markdown';
import { getProviderId, getModelLocalId } from '../utils';

type ModelSettingsProps = {
  rmRegistry: IRenderMimeRegistry;
  label: string;
  onChange: (settings: IModelSettings) => void;
  modelKind: 'chat' | 'completions';
};

export interface IModelSettings {
  fields: Record<string, any>;
  apiKeys: Record<string, string>;
  emGlobalId: string | null;
  lmGlobalId: string | null;
}

/**
 * Component that returns the settings view in the chat panel.
 */
export function ModelSettings(props: ModelSettingsProps): JSX.Element {
  // state fetched on initial render
  const server = useServerInfo();

  // initialize alert helper
  const apiKeysAlert = useStackingAlert();

  // user inputs
  const [lmProvider, setLmProvider] =
    useState<AiService.ListProvidersEntry | null>(null);
  const [showLmLocalId, setShowLmLocalId] = useState<boolean>(false);
  const [helpMarkdown, setHelpMarkdown] = useState<string | null>(null);
  const [lmLocalId, setLmLocalId] = useState<string>('');
  const lmGlobalId = useMemo<IModelSettings['lmGlobalId']>(() => {
    if (!lmProvider) {
      return null;
    }

    return lmProvider.id + ':' + lmLocalId;
  }, [lmProvider, lmLocalId]);

  const [emGlobalId, setEmGlobalId] =
    useState<IModelSettings['emGlobalId']>(null);
  const emProvider = useMemo<AiService.ListProvidersEntry | null>(() => {
    if (emGlobalId === null || server.state !== ServerInfoState.Ready) {
      return null;
    }

    return getProvider(emGlobalId, server.emProviders);
  }, [emGlobalId, server]);

  const [apiKeys, setApiKeys] = useState<IModelSettings['apiKeys']>({});
  const [fields, setFields] = useState<IModelSettings['fields']>({});

  /**
   * Effect: initialize inputs after fetching server info.
   */
  useEffect(() => {
    if (server.state !== ServerInfoState.Ready) {
      return;
    }
    const kind = props.modelKind;

    setLmLocalId(server[kind].lmLocalId);
    setEmGlobalId(
      kind === 'chat'
        ? server.config.embeddings_provider_id
        : server.config.completions_embeddings_provider_id
    );
    setHelpMarkdown(server[kind].lmProvider?.help ?? null);
    if (server[kind].lmProvider?.registry) {
      setShowLmLocalId(true);
    }
    setLmProvider(server[kind].lmProvider);
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
    setFields(currFields);
  }, [server, lmProvider]);

  useEffect(() => {
    props.onChange({
      fields,
      apiKeys,
      lmGlobalId,
      emGlobalId
    });
  }, [lmProvider, emProvider, apiKeys, fields]);

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
      <>
        <Alert severity="error">
          {server.error ||
            'An unknown error occurred. Check the console for more details.'}
        </Alert>
      </>
    );
  }

  return (
    <>
      {/* Language model section */}
      <h2 className="jp-ai-ChatSettings-header">{props.label}</h2>
      <Select
        value={lmProvider?.registry ? lmProvider.id + ':*' : lmGlobalId}
        label={props.label}
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
          setHelpMarkdown(nextLmProvider?.help ?? null);
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
            .filter(lm =>
              props.modelKind === 'completions'
                ? lmp.completion_models.includes(lm)
                : lmp.chat_models.includes(lm)
            )
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
      {helpMarkdown && (
        <RendermimeMarkdown
          rmRegistry={props.rmRegistry}
          markdownStr={helpMarkdown}
        />
      )}
      {lmGlobalId && (
        <ModelFields
          fields={lmProvider?.fields}
          values={fields}
          onChange={setFields}
        />
      )}

      {/* Embedding model section */}
      <h2 className="jp-ai-ChatSettings-header">Embedding model</h2>
      <Select
        value={emGlobalId}
        label="Embedding model"
        onChange={e => {
          const emGid = e.target.value === 'null' ? null : e.target.value;
          setEmGlobalId(emGid);
        }}
        MenuProps={{ sx: { maxHeight: '50%', minHeight: 400 } }}
      >
        <MenuItem value="null">None</MenuItem>
        {server.emProviders.providers.map(emp =>
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
    </>
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
