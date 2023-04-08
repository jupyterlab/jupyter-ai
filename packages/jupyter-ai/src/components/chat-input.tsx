import React from 'react';

import {
  Box,
  IconButton,
  Input,
  SxProps,
  Theme,
  FormGroup,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

type ChatInputProps = {
  loading: boolean;
  value: string;
  onChange: (newValue: string) => unknown;
  onSend: () => unknown;
  hasSelection: boolean;
  includeSelection: boolean;
  toggleIncludeSelection: () => unknown;
  replaceSelection: boolean;
  toggleReplaceSelection: () => unknown;
  sx?: SxProps<Theme>;
};

export function ChatInput(props: ChatInputProps): JSX.Element {
  return (
    <Box sx={props.sx}>
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
      {props.hasSelection && (
        <FormGroup sx={{ display: 'flex', flexDirection: 'row' }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={props.includeSelection}
                onChange={props.toggleIncludeSelection}
              />
            }
            label="Include selection"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={props.replaceSelection}
                onChange={props.toggleReplaceSelection}
              />
            }
            label="Replace selection"
          />
        </FormGroup>
      )}
    </Box>
  );
}
