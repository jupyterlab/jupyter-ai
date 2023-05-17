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
  helperText: JSX.Element
  sx?: SxProps<Theme>;
};

export function ChatInput(props: ChatInputProps): JSX.Element {
  
  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter' && event.shiftKey) {
      props.onSend();
      event.stopPropagation();
      event.preventDefault();
    }
  }
  return (
    <Box sx={props.sx}>
      <Box sx={{ display: 'flex'}}>
        <TextField
          value={props.value}
          onChange={e => props.onChange(e.target.value)}
          fullWidth
          variant="outlined"
          multiline
          onKeyDown={handleKeyDown}
          placeholder='Ask Jupyternaut anything'
          InputProps={{
            endAdornment: (
               <InputAdornment position="end">
                  <IconButton
                    size="small"
                    color="primary"
                    onClick={props.onSend}
                    disabled={!props.value.trim().length}
                    title='Send message (SHIFT+ENTER)'
                  >
                    <SendIcon />
                  </IconButton>
               </InputAdornment>
            )
         }}
         FormHelperTextProps={{
          sx: {marginLeft: 'auto', marginRight: 0}
         }}
         helperText={props.value.length > 2 ? props.helperText : ' '}
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
