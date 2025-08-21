import React, { useEffect, useState } from 'react';

import { Box } from '@mui/system';
import { IconButton, Tooltip } from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { IJaiCompletionProvider } from '../tokens';
import { ModelIdInput } from './settings/model-id-input';
import { ModelParametersInput } from './settings/model-parameters-input';
import { SecretsSection } from './settings/secrets-section';

type ChatSettingsProps = {
  rmRegistry: IRenderMimeRegistry;
  completionProvider: IJaiCompletionProvider | null;
  openInlineCompleterSettings: () => void;
};

const MODEL_ID_HELP = (
  <p>
    You may provide any model ID accepted by LiteLLM. Details can be found from
    the{' '}
    <a
      href="https://docs.litellm.ai/docs/providers"
      target="_blank"
      rel="noopener noreferrer"
    >
      LiteLLM documentation
    </a>
    .
  </p>
);

/**
 * Component that returns the settings view in the chat panel.
 */
export function ChatSettings(props: ChatSettingsProps): JSX.Element {
  const [completionModel, setCompletionModel] = useState<string | null>(null);
  const [chatModel, setChatModel] = useState<string | null>(null);
  const [isCompleterEnabled, setIsCompleterEnabled] = useState(
    props.completionProvider && props.completionProvider.isEnabled()
  );

  /**
   * Effect: Listen to JupyterLab completer settings updates on initial render
   * and update the `isCompleterEnabled` state variable accordingly.
   */
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

  return (
    <Box
      className="jp-ai-ChatSettings"
      sx={{
        '& .MuiAlert-root': {
          marginTop: 2
        }
      }}
    >
      {/* SECTION: Chat model */}
      <h2 className="jp-ai-ChatSettings-header">Chat model</h2>
      <p>Configure the language model used by Jupyternaut in chats.</p>
      {MODEL_ID_HELP}
      <ModelIdInput
        modality="chat"
        label="Chat model ID"
        placeholder="e.g. 'anthropic/claude-3-5-haiku-latest'"
        onModelIdFetch={modelId => setChatModel(modelId)}
      />

      {/* SECTION: Completion model */}
      {/* TODO: Re-enable this when the completion backend works with LiteLLM. */}
      <Box sx={{ display: 'none' }}>
        <h2 className="jp-ai-ChatSettings-header">
          Completion model
          <CompleterSettingsButton
            provider={props.completionProvider}
            openSettings={props.openInlineCompleterSettings}
            isCompleterEnabled={isCompleterEnabled}
            hasCompletionModel={!!completionModel}
          />
        </h2>
        <p>
          Configure the language model used to generate inline completions when
          editing documents in JupyterLab.
        </p>
        {MODEL_ID_HELP}
        <ModelIdInput
          modality="completion"
          label="Completion model ID"
          placeholder="e.g. 'anthropic/claude-3-5-haiku-latest'"
          onModelIdFetch={modelId => {
            setCompletionModel(modelId);
          }}
        />
      </Box>

      {/* Model parameters section */}
      <h2 className="jp-ai-ChatSettings-header">Model parameters</h2>
      <p>Configure additional parameters for the language model.</p>
      <ModelParametersInput modelId={chatModel} />

      {/* SECTION: Secrets (and API keys) */}
      <h2 className="jp-ai-ChatSettings-header">Secrets and API keys</h2>
      <SecretsSection />
    </Box>
  );
}

function CompleterSettingsButton(props: {
  hasCompletionModel: boolean;
  provider: IJaiCompletionProvider | null;
  isCompleterEnabled: boolean | null;
  openSettings: () => void;
}): JSX.Element {
  if (props.hasCompletionModel && !props.isCompleterEnabled) {
    return (
      <Tooltip
        title={
          'A completion model is selected, but ' +
          (props.provider === null
            ? 'the inline completion plugin is not available. Update to JupyterLab 4.1+ to use inline completions.'
            : 'inline completions are disabled. Click the icon to open the inline completion settings.')
        }
      >
        <IconButton onClick={props.openSettings}>
          <WarningAmberIcon />
        </IconButton>
      </Tooltip>
    );
  }
  return (
    <Tooltip title="Open inline completion settings">
      <IconButton onClick={props.openSettings}>
        <SettingsIcon />
      </IconButton>
    </Tooltip>
  );
}
