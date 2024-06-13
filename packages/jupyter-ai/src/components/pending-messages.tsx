import React, { useState, useEffect } from 'react';

import { Box } from '@mui/material';
import { AiService } from '../handler';
import { ChatMessageHeader } from './chat-messages';

const PENDING_MESSAGE_CLASS = 'jp-ai-pending-message';

type PendingMessagesProps = {
  messages: AiService.PendingMessage[];
};

type PendingMessageElementProps = {
  text: string;
  ellipsis: boolean;
};

type PendingMessageGroup = {
  // Creating lastMessage as an AgentChatMessage
  // as a hacky way to reuse ChatMessageHeader
  // TODO: Refactor ChatMessageHeader to accept PendingMessage
  lastMessage: AiService.AgentChatMessage;
  messages: AiService.PendingMessage[];
};

function PendingMessageElement(props: PendingMessageElementProps): JSX.Element {
  let text = props.text;
  if (props.ellipsis) {
    const [dots, setDots] = useState('');

    useEffect(() => {
      const interval = setInterval(() => {
        setDots(dots => (dots.length < 3 ? dots + '.' : ''));
      }, 500);

      return () => clearInterval(interval);
    }, []);
    text = props.text + dots;
  }
  return (
    <div>
      {text.split('\n').map((line, index) => (
        <p key={index}>{line}</p>
      ))}
    </div>
  );
}

export function PendingMessages(props: PendingMessagesProps): JSX.Element {
  if (props.messages.length === 0) {
    return <></>;
  }

  const [timestamps, setTimestamps] = useState<Record<string, string>>({});
  const personaGroups = groupMessages(props.messages);
  /**
   * Effect: update cached timestamp strings upon receiving a new message.
   */
  useEffect(() => {
    const newTimestamps: Record<string, string> = { ...timestamps };
    let timestampAdded = false;

    for (const message of props.messages) {
      if (!(message.id in newTimestamps)) {
        // Use the browser's default locale
        newTimestamps[message.id] = new Date(message.time * 1000) // Convert message time to milliseconds
          .toLocaleTimeString([], {
            hour: 'numeric', // Avoid leading zero for hours; we don't want "03:15 PM"
            minute: '2-digit'
          });

        timestampAdded = true;
      }
    }
    if (timestampAdded) {
      setTimestamps(newTimestamps);
    }
  }, [personaGroups.map(group => group.lastMessage)]);

  return (
    <Box
      sx={{
        borderTop: '1px solid var(--jp-border-color2)',
        '& > :not(:last-child)': {
          borderBottom: '1px solid var(--jp-border-color2)'
        }
      }}
    >
      {personaGroups.map((group, i) => (
        <Box key={i} sx={{ padding: 4 }}>
          <ChatMessageHeader
            message={group.lastMessage}
            timestamp={timestamps[group.lastMessage.id]}
            sx={{ marginBottom: 3 }}
          />
          {group.messages.map((message, j) => (
            <Box
              className={PENDING_MESSAGE_CLASS}
              key={j}
              sx={{ marginBottom: 1 }}
            >
              <PendingMessageElement
                text={message.body}
                ellipsis={message.ellipsis}
              />
            </Box>
          ))}
        </Box>
      ))}
    </Box>
  );
}

function groupMessages(
  messages: AiService.PendingMessage[]
): PendingMessageGroup[] {
  const groups: PendingMessageGroup[] = [];
  const personaMap = new Map<string, AiService.PendingMessage[]>();
  for (const message of messages) {
    if (!personaMap.has(message.persona.name)) {
      personaMap.set(message.persona.name, []);
    }
    personaMap.get(message.persona.name)?.push(message);
  }
  // create a dummy agent message for each persona group
  for (const messages of personaMap.values()) {
    const lastMessage = messages[messages.length - 1];
    groups.push({
      lastMessage: {
        type: 'agent',
        id: lastMessage.id,
        time: lastMessage.time,
        body: '',
        reply_to: '',
        persona: lastMessage.persona
      },
      messages
    });
  }
  return groups;
}
