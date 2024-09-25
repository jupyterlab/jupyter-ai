import React, { useState, useEffect } from 'react';

import { Box, Typography } from '@mui/material';
import { AiService } from '../handler';
import { ChatMessageHeader } from './chat-messages';
import { ChatHandler } from '../chat_handler';

type PendingMessagesProps = {
  messages: AiService.PendingMessage[];
  chatHandler: ChatHandler;
};

type PendingMessageElementProps = {
  text: string;
  ellipsis: boolean;
};

function PendingMessageElement(props: PendingMessageElementProps): JSX.Element {
  const [dots, setDots] = useState('');

  useEffect(() => {
    const interval = setInterval(() => {
      setDots(dots => (dots.length < 3 ? dots + '.' : ''));
    }, 500);

    return () => clearInterval(interval);
  }, []);

  let text = props.text;
  if (props.ellipsis) {
    text = props.text + dots;
  }

  return (
    <Box>
      {text.split('\n').map((line, index) => (
        <Typography key={index}>{line}</Typography>
      ))}
    </Box>
  );
}

export function PendingMessages(
  props: PendingMessagesProps
): JSX.Element | null {
  const [timestamp, setTimestamp] = useState<string>('');
  const [agentMessage, setAgentMessage] =
    useState<AiService.AgentChatMessage | null>(null);

  useEffect(() => {
    if (props.messages.length === 0) {
      setAgentMessage(null);
      setTimestamp('');
      return;
    }
    const lastMessage = props.messages[props.messages.length - 1];
    setAgentMessage({
      type: 'agent',
      id: lastMessage.id,
      time: lastMessage.time,
      body: '',
      reply_to: '',
      persona: lastMessage.persona,
      metadata: {}
    });

    // timestamp format copied from ChatMessage
    const newTimestamp = new Date(lastMessage.time * 1000).toLocaleTimeString(
      [],
      {
        hour: 'numeric',
        minute: '2-digit'
      }
    );
    setTimestamp(newTimestamp);
  }, [props.messages]);

  if (!agentMessage) {
    return null;
  }

  return (
    <Box
      sx={{
        padding: 4,
        borderTop: '1px solid var(--jp-border-color2)'
      }}
    >
      <ChatMessageHeader
        message={agentMessage}
        chatHandler={props.chatHandler}
        timestamp={timestamp}
        sx={{
          marginBottom: 4
        }}
      />
      <Box
        sx={{
          marginBottom: 1,
          paddingRight: 0,
          color: 'var(--jp-ui-font-color2)',
          '& > :not(:last-child)': {
            marginBottom: '2em'
          }
        }}
      >
        {props.messages.map(message => (
          <PendingMessageElement
            key={message.id}
            text={message.body}
            ellipsis={message.ellipsis}
          />
        ))}
      </Box>
    </Box>
  );
}
