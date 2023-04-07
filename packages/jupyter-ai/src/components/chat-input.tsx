import React from 'react';

import { Box, IconButton, Input } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

type ChatInputProps = {
  loading: boolean;
  value: string;
  onChange: (newValue: string) => unknown;
  onSend: () => unknown;
};

export function ChatInput(props: ChatInputProps): JSX.Element {
  return (
    <Box sx={{ display: 'flex' }}>
      <Input
        value={props.value}
        onChange={e => props.onChange(e.target.value)}
        multiline
        sx={{ flexGrow: 1 }}
      />
      <IconButton
        size="large"
        color="primary"
        onClick={props.onSend}
        disabled={props.loading || !props.value.trim().length}
      >
        <SendIcon />
      </IconButton>
    </Box>
  );
}
