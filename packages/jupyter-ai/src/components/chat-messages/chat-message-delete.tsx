import React from 'react';
import { SxProps } from '@mui/material';
import { Close } from '@mui/icons-material';

import { AiService } from '../../handler';
import { ChatHandler } from '../../chat_handler';
import { TooltippedIconButton } from '../mui-extras/tooltipped-icon-button';

type DeleteButtonProps = {
  message: AiService.ChatMessage;
  chatHandler: ChatHandler;
  sx?: SxProps;
};

export function ChatMessageDelete(props: DeleteButtonProps): JSX.Element {
  const request: AiService.ClearRequest = {
    type: 'clear',
    target: props.message.id,
    after: false
  };
  return (
    <TooltippedIconButton
      onClick={() => props.chatHandler.sendMessage(request)}
      sx={props.sx}
      tooltip="Delete this exchange"
    >
      <Close />
    </TooltippedIconButton>
  );
}

export default ChatMessageDelete;
