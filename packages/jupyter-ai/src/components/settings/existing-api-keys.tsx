import React, { useState } from 'react';
import { Alert, Box, IconButton, Typography } from '@mui/material';
import { Edit, Delete } from '@mui/icons-material';
import { AsyncIconButton } from '../mui-extras/async-icon-button';

import { AiService } from '../../handler';

export type ExistingApiKeysProps = {
  apiKeys: string[];
};

enum DeleteStatus {
  Initial,
  Success,
  Failure
}

export function ExistingApiKeys(props: ExistingApiKeysProps): JSX.Element {
  const [deleteStatus, setDeleteStatus] = useState<DeleteStatus>(
    DeleteStatus.Initial
  );
  const [emsg, setEmsg] = useState<string>();

  return (
    <Box>
      {deleteStatus === DeleteStatus.Failure && (
        <Alert severity="error">{emsg}</Alert>
      )}
      {deleteStatus === DeleteStatus.Success && (
        <Alert severity="success">API key deleted successfully.</Alert>
      )}
      {props.apiKeys.map((apiKey, idx) => (
        <ExistingApiKey
          apiKey={apiKey}
          key={idx}
          onSuccess={() => {
            setDeleteStatus(DeleteStatus.Success);
          }}
          onError={newEmsg => {
            setDeleteStatus(DeleteStatus.Failure);
            setEmsg(newEmsg);
          }}
        />
      ))}
    </Box>
  );
}

type ExistingApiKeyProps = {
  apiKey: string;
  onError: (emsg: string) => unknown;
  onSuccess: () => unknown;
};

function ExistingApiKey(props: ExistingApiKeyProps) {
  // const [apiKeyInput, setApiKeyInput] = useState('');

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}
    >
      <Typography>
        <pre style={{ margin: 0 }}>{props.apiKey}</pre>
      </Typography>
      <Box>
        <IconButton>
          <Edit />
        </IconButton>
        <AsyncIconButton
          onClick={() => AiService.deleteApiKey(props.apiKey)}
          onError={props.onError}
          onSuccess={props.onSuccess}
        >
          <Delete />
        </AsyncIconButton>
      </Box>
    </Box>
  );
}
