import React, { useState, useEffect } from 'react';

import { Avatar, Box, Typography } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { ServerConnection } from '@jupyterlab/services';
// TODO: delete jupyternaut from frontend package

import { AiService } from '../handler';
import { RendermimeMarkdown } from './rendermime-markdown';
import { useCollaboratorsContext } from '../contexts/collaborators-context';

type ChatMessagesProps = {
  rmRegistry: IRenderMimeRegistry;
  messages: AiService.ChatMessage[];
};

type ChatMessageHeaderProps = {
  message: AiService.ChatMessage;
  timestamp: string;
  sx?: SxProps<Theme>;
};

function sortMessages(
  messages: AiService.ChatMessage[]
): AiService.ChatMessage[] {
  const timestampsById: Record<string, number> = {};
  for (const message of messages) {
    timestampsById[message.id] = message.time;
  }

  return [...messages].sort((a, b) => {
    /**
     * Use the *origin timestamp* as the primary sort key. This ensures that
     * each agent reply is grouped with the human message that triggered it.
     *
     * - If the message is from an agent, the origin timestamp is the timestamp
     * of the message it is replying to.
     *
     * - Otherwise, the origin timestamp is the *message timestamp*, i.e.
     * `message.time` itself.
     */

    const aOriginTimestamp =
      a.type === 'agent' && a.reply_to in timestampsById
        ? timestampsById[a.reply_to]
        : a.time;
    const bOriginTimestamp =
      b.type === 'agent' && b.reply_to in timestampsById
        ? timestampsById[b.reply_to]
        : b.time;

    /**
     * Use the message timestamp as a secondary sort key. This ensures that each
     * agent reply is shown after the human message that triggered it.
     */
    const aMessageTimestamp = a.time;
    const bMessageTimestamp = b.time;

    return (
      aOriginTimestamp - bOriginTimestamp ||
      aMessageTimestamp - bMessageTimestamp
    );
  });
}

export function ChatMessageHeader(props: ChatMessageHeaderProps): JSX.Element {
  const collaborators = useCollaboratorsContext();

  const sharedStyles: SxProps<Theme> = {
    height: '24px',
    width: '24px'
  };

  let avatar: JSX.Element;
  if (props.message.type === 'human') {
    const bgcolor = collaborators?.[props.message.client.username]?.color;
    avatar = (
      <Avatar
        sx={{
          ...sharedStyles,
          ...(bgcolor && { bgcolor })
        }}
      >
        <Typography
          sx={{
            fontSize: 'var(--jp-ui-font-size1)',
            color: 'var(--jp-ui-inverse-font-color1)'
          }}
        >
          {props.message.client.initials}
        </Typography>
      </Avatar>
    );
  } else {
    const baseUrl = ServerConnection.makeSettings().baseUrl;
    const avatar_url = baseUrl + props.message.persona.avatar_route;
    avatar = (
      <Avatar sx={{ ...sharedStyles, bgcolor: 'var(--jp-layout-color-1)' }}>
        <img src={avatar_url} />
      </Avatar>
    );
  }

  const name =
    props.message.type === 'human'
      ? props.message.client.display_name
      : props.message.persona.name;

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        '& > :not(:last-child)': {
          marginRight: 3
        },
        ...props.sx
      }}
    >
      {avatar}
      <Box
        sx={{
          display: 'flex',
          flexGrow: 1,
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <Typography sx={{ fontWeight: 700, color: 'var(--jp-ui-font-color1)' }}>
          {name}
        </Typography>
        <Typography
          sx={{
            fontSize: '0.8em',
            color: 'var(--jp-ui-font-color2)',
            fontWeight: 300
          }}
        >
          {props.timestamp}
        </Typography>
      </Box>
    </Box>
  );
}

export function ChatMessages(props: ChatMessagesProps): JSX.Element {
  const [timestamps, setTimestamps] = useState<Record<string, string>>({});
  const [sortedMessages, setSortedMessages] = useState<AiService.ChatMessage[]>(
    []
  );

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
  }, [props.messages]);

  useEffect(() => {
    setSortedMessages(sortMessages(props.messages));
  }, [props.messages]);

  return (
    <Box
      sx={{
        '& > :not(:last-child)': {
          borderBottom: '1px solid var(--jp-border-color2)'
        }
      }}
    >
      {sortedMessages.map(message => {
        // render selection in HumanChatMessage, if any
        const markdownStr =
          message.type === 'human' && message.selection
            ? message.body + '\n\n```\n' + message.selection.source + '\n```\n'
            : message.body;
        return (
          <Box key={message.id} sx={{ padding: 4 }}>
            <ChatMessageHeader
              message={message}
              timestamp={timestamps[message.id]}
              sx={{ marginBottom: 3 }}
            />
            <RendermimeMarkdown
              rmRegistry={props.rmRegistry}
              markdownStr={markdownStr}
            />
          </Box>
        );
      })}
    </Box>
  );
}
