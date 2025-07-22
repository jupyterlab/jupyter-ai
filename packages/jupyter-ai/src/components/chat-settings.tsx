import React, { useEffect, useState } from 'react';

import { Box } from '@mui/system';
import { IconButton, Tooltip } from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { IJaiCompletionProvider } from '../tokens';
import { ModelIdInput } from './settings/model-id-input';

type ChatSettingsProps = {
  rmRegistry: IRenderMimeRegistry;
  completionProvider: IJaiCompletionProvider | null;
  openInlineCompleterSettings: () => void;
};

/**
 * Component that returns the settings view in the chat panel.
 */
export function ChatSettings(props: ChatSettingsProps): JSX.Element {
  const [completionModel, setCompletionModel] = useState<string | null>(null);
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
      sx={{
        padding: '0 12px 12px',
        boxSizing: 'border-box',
        '& .MuiAlert-root': {
          marginTop: 2
        },
        overflowY: 'auto'
      }}
    >
      {/* Chat model section */}
      <h2 className="jp-ai-ChatSettings-header">Chat model</h2>
      <p>Configure the language model used by Jupyternaut in chats.</p>
      <ModelIdInput
        modality="chat"
        label="Chat model ID"
        placeholder="e.g. 'anthropic/claude-3-5-haiku-latest'"
      />

      {/* Embedding model section */}
      {/* TODO */}

      {/* Completion model section */}
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
      <ModelIdInput
        modality="completion"
        label="Completion model ID"
        placeholder="e.g. 'anthropic/claude-3-5-haiku-latest'"
        onModelIdFetch={latestChatModelId => {
          setCompletionModel(latestChatModelId);
        }}
      />
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
