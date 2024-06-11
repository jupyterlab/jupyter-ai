import React from 'react';
import SendIcon from '@mui/icons-material/Send';

import { TooltippedIconButton } from '../mui-extras/tooltipped-icon-button';

export type SendButtonProps = {
  onSend: () => unknown;
  sendWithShiftEnter: boolean;
  currSlashCommand: string | null;
  inputExists: boolean;
  activeCellHasError: boolean;
};

export function SendButton(props: SendButtonProps): JSX.Element {
  const disabled =
    props.currSlashCommand === '/fix'
      ? !props.inputExists || !props.activeCellHasError
      : !props.inputExists;

  const defaultTooltip = props.sendWithShiftEnter
    ? 'Send message (SHIFT+ENTER)'
    : 'Send message (ENTER)';

  const tooltip =
    props.currSlashCommand === '/fix' && !props.activeCellHasError
      ? '/fix requires a code cell with an error output selected'
      : !props.inputExists
      ? 'Message must not be empty'
      : defaultTooltip;

  return (
    <TooltippedIconButton
      onClick={() => props.onSend()}
      disabled={disabled}
      tooltip={tooltip}
      iconButtonProps={{
        size: 'small',
        color: 'primary',
        title: defaultTooltip
      }}
    >
      <SendIcon />
    </TooltippedIconButton>
  );
}
