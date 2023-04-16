import React, { useState, useEffect } from 'react';

import { Avatar, Box, Typography } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';
import PsychologyIcon from '@mui/icons-material/Psychology';
import { formatDistanceToNowStrict, fromUnixTime } from 'date-fns';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

import { ChatCodeView } from './chat-code-view';
import { AiService } from '../handler';
import { useCollaboratorsContext } from '../contexts/collaborators-context';

type ChatMessagesProps = {
  messages: AiService.ChatMessage[];
};

type ChatMessageHeaderProps = {
  message: AiService.ChatMessage;
  timestamp: string;
  sx?: SxProps<Theme>;
};

export function ChatMessageHeader(props: ChatMessageHeaderProps) {
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
    avatar = (
      <Avatar sx={{ ...sharedStyles, bgcolor: 'var(--jp-jupyter-icon-color)' }}>
        <PsychologyIcon />
      </Avatar>
    );
  }

  const name =
    props.message.type === 'human'
      ? props.message.client.display_name
      : 'Jupyter AI';

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
        <Typography sx={{ fontWeight: 700, color: 'var(--jp-ui-font-color1)' }}>{name}</Typography>
        <Typography sx={{ fontSize: '0.8em', color: 'var(--jp-ui-font-color2)', fontWeight: 300 }}>
          {props.timestamp}
        </Typography>
      </Box>
    </Box>
  );
}

export function ChatMessages(props: ChatMessagesProps) {
  const [timestamps, setTimestamps] = useState<Record<string, string>>({});

  /**
   * Effect: update cached timestamp strings upon receiving a new message and
   * every 5 seconds after that.
   */
  useEffect(() => {
    function updateTimestamps() {
      const newTimestamps: Record<string, string> = {};
      for (const message of props.messages) {
        newTimestamps[message.id] =
          formatDistanceToNowStrict(fromUnixTime(message.time)) + ' ago';
      }
      setTimestamps(newTimestamps);
    }

    updateTimestamps();
    const intervalId = setInterval(updateTimestamps, 5000);
    return () => {
      clearInterval(intervalId);
    };
  }, [props.messages]);

  return (
    <Box
      sx={{ '& > :not(:last-child)': { borderBottom: '1px solid var(--jp-border-color2)' } }}
    >
      {props.messages.map((message, i) => (
        // extra div needed to ensure each bubble is on a new line
        <Box key={i} sx={{ padding: 4 }}>
          <ChatMessageHeader
            message={message}
            timestamp={timestamps[message.id]}
            sx={{ marginBottom: 3 }}
          />
          <ReactMarkdown
            // We are using the jp-RenderedHTMLCommon class here to get the default Jupyter
            // markdown styling and then overriding any CSS to make it more compact.
            className="jp-RenderedHTMLCommon jp-ai-react-markdown"
            components={{
              code: ChatCodeView
            }}
            remarkPlugins={[remarkMath]}
            rehypePlugins={[rehypeKatex]}
          >
            {message.body}
          </ReactMarkdown>
        </Box>
      ))}
    </Box>
  );
}
