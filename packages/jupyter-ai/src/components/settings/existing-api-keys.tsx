import React from 'react';
import { Box, IconButton, Typography } from '@mui/material';
import { Edit, DeleteOutline } from '@mui/icons-material';
import { AsyncIconButton } from '../mui-extras/async-icon-button';

import { AiService } from '../../handler';
import { StackingAlert } from '../mui-extras/stacking-alert';

export type ExistingApiKeysProps = {
  alert: StackingAlert;
  apiKeys: string[];
  onSuccess: () => unknown;
};

export function ExistingApiKeys(props: ExistingApiKeysProps): JSX.Element {
  return (
    <Box>
      {props.apiKeys.map((apiKey, idx) => (
        <ExistingApiKey
          apiKey={apiKey}
          key={idx}
          onSuccess={() => {
            props.alert.show('success', 'API key deleted successfully.');
            props.onSuccess();
          }}
          onError={newEmsg => {
            props.alert.show('error', newEmsg);
          }}
        />
      ))}
      {props.alert.jsx}
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
          confirm={true}
        >
          <DeleteOutline color="error" />
        </AsyncIconButton>
      </Box>
    </Box>
  );
}
