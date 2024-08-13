import React from 'react';
import { IconButton, SxProps } from '@mui/material';
import { Close } from '@mui/icons-material';

import { AiService } from '../../handler';
import { ChatHandler } from '../../chat_handler';

type DeleteButtonProps = {
  message: AiService.ChatMessage;
  chatHandler: ChatHandler;
  sx?: SxProps;
};

export function ChatMessageDelete(props: DeleteButtonProps): JSX.Element {
  const request: AiService.ClearRequest = {
    type: 'clear',
    target: props.message.id
  };
  return (
    <IconButton
      onClick={() => props.chatHandler.sendMessage(request)}
      sx={props.sx}
    >
      <Close />
    </IconButton>
  );
}

export default ChatMessageDelete;
