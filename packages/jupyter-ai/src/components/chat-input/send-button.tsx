import React from 'react';
import { Box } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import StopIcon from '@mui/icons-material/Stop';

import { TooltippedButton } from '../mui-extras/tooltipped-button';

const FIX_TOOLTIP = '/fix requires an active code cell with an error';

export type SendButtonProps = {
  onStop: () => unknown;
  onSend: () => unknown;
  sendWithShiftEnter: boolean;
  currSlashCommand: string | null;
  inputExists: boolean;
  activeCellHasError: boolean;
  /**
   * Whether the backend is streaming a reply to any message sent by the current
   * user.
   */
  streamingReplyHere: boolean;
};

export function SendButton(props: SendButtonProps): JSX.Element {
  let action: 'send' | 'stop' | 'fix' = props.inputExists
    ? 'send'
    : props.streamingReplyHere
    ? 'stop'
    : 'send';
  if (props.currSlashCommand === '/fix') {
    action = 'fix';
  }

  let disabled = false;
  if (action === 'send' && !props.inputExists) {
    disabled = true;
  }
  if (action === 'fix' && !props.activeCellHasError) {
    disabled = true;
  }

  const defaultTooltip = props.sendWithShiftEnter
    ? 'Send message (SHIFT+ENTER)'
    : 'Send message (ENTER)';

  const tooltip =
    action === 'fix' && !props.activeCellHasError
      ? FIX_TOOLTIP
      : action === 'stop'
      ? 'Stop streaming'
      : !props.inputExists
      ? 'Message must not be empty'
      : defaultTooltip;


  return (
    <Box sx={{ display: 'flex', flexWrap: 'nowrap' }}>
      <TooltippedButton
        onClick={() => (action === 'stop' ? props.onStop() : props.onSend())}
        disabled={disabled}
        tooltip={tooltip}
        buttonProps={{
          size: 'small',
          title: defaultTooltip,
          variant: 'contained'
        }}
        sx={{
          minWidth: 'unset',
          borderRadius: '2px 0px 0px 2px'
        }}
      >
        {action === 'stop' ? <StopIcon /> : <SendIcon />}
      </TooltippedButton>
    </Box>
  );
}
