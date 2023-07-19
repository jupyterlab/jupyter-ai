import React from 'react';

import {
  Box,
  SxProps,
  TextField,
  Theme,
  FormGroup,
  FormControlLabel,
  Checkbox,
  IconButton,
  InputAdornment
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

type ChatInputProps = {
  value: string;
  onChange: (newValue: string) => unknown;
  onSend: () => unknown;
  hasSelection: boolean;
  includeSelection: boolean;
  toggleIncludeSelection: () => unknown;
  replaceSelection: boolean;
  toggleReplaceSelection: () => unknown;
  sendWithShiftEnter: boolean;
  sx?: SxProps<Theme>;
};

export function ChatInput(props: ChatInputProps): JSX.Element {
  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (
      event.key === 'Enter' &&
      ((props.sendWithShiftEnter && event.shiftKey) ||
        (!props.sendWithShiftEnter && !event.shiftKey))
    ) {
      props.onSend();
      event.stopPropagation();
      event.preventDefault();
    }
  }

  // Set the helper text based on whether Shift+Enter is used for sending.
  const helperText = props.sendWithShiftEnter ? (
    <span>
      Press <b>Shift</b>+<b>Enter</b> to send message
    </span>
  ) : (
    <span>
      Press <b>Shift</b>+<b>Enter</b> to add a new line
    </span>
  );

  return (
    <Box sx={props.sx}>
      <Box sx={{ display: 'flex' }}>
        <TextField
          value={props.value}
          onChange={e => props.onChange(e.target.value)}
          fullWidth
          variant="outlined"
          multiline
          onKeyDown={handleKeyDown}
          placeholder="Ask Jupyternaut"
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  size="small"
                  color="primary"
                  onClick={props.onSend}
                  disabled={!props.value.trim().length}
                  title="Send message (SHIFT+ENTER)"
                >
                  <SendIcon />
                </IconButton>
              </InputAdornment>
            )
          }}
          FormHelperTextProps={{
            sx: { marginLeft: 'auto', marginRight: 0 }
          }}
          helperText={props.value.length > 2 ? helperText : ' '}
        />
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
