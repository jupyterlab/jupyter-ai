import React, { useState, useEffect } from 'react';

import { Box } from '@mui/material';
import { AiService } from '../handler';
import { ChatMessageHeader } from './chat-messages';

type PendingMessagesProps = {
  messages: AiService.PendingMessage[];
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
    <div>
      {text.split('\n').map((line, index) => (
        <p key={index} style={{ lineHeight: 0.6 }}>
          {line}
        </p>
      ))}
    </div>
  );
}

export function PendingMessages(
  props: PendingMessagesProps
): JSX.Element | null {
  if (props.messages.length === 0) {
    return null;
  }

  const [timestamp, setTimestamp] = useState<string>('');
  const lastMessage = props.messages[props.messages.length - 1];
  const agentMessage: AiService.AgentChatMessage = {
    type: 'agent',
    id: lastMessage.id,
    time: lastMessage.time,
    body: '',
    reply_to: '',
    persona: lastMessage.persona
  };

  useEffect(() => {
    // timestamp format copied from ChatMessage
    const newTimestamp = new Date(agentMessage.time * 1000).toLocaleTimeString(
      [],
      {
        hour: 'numeric',
        minute: '2-digit'
      }
    );
    setTimestamp(newTimestamp);
  }, [agentMessage]);

  return (
    <Box
      sx={{
        borderTop: '1px solid var(--jp-border-color2)',
        '& > :not(:last-child)': {
          borderBottom: '1px solid var(--jp-border-color2)'
        }
      }}
    >
      <Box sx={{ padding: 4 }}>
        <ChatMessageHeader
          message={agentMessage}
          timestamp={timestamp}
          sx={{ marginBottom: 4 }}
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
          {props.messages.map((message) => (
            <PendingMessageElement
              key={message.id}
              text={message.body}
              ellipsis={message.ellipsis}
            />
          ))}
        </Box>
      </Box>
    </Box>
  );
}
