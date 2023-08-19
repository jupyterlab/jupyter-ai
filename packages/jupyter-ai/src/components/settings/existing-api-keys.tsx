import React from 'react';
import { Box, IconButton, Typography } from '@mui/material';
import { Edit, Delete } from '@mui/icons-material';

export type ExistingApiKeysProps = {
  apiKeys: string[];
};

export function ExistingApiKeys(props: ExistingApiKeysProps): JSX.Element {
  return (
    <>
      {props.apiKeys.map((apiKey, idx) => (
        <ExistingApiKey apiKey={apiKey} key={idx} />
      ))}
    </>
  );
}

type ExistingApiKeyProps = {
  apiKey: string;
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
        <IconButton>
          <Delete />
        </IconButton>
      </Box>
    </Box>
  );
}
