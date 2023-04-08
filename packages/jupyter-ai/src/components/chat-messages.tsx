import React from 'react';

import { Avatar, Box, useTheme } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';
import PsychologyIcon from '@mui/icons-material/Psychology';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

import { ChatCodeView } from './chat-code-view';

type ChatMessagesProps = {
  sender: 'self' | 'ai' | string;
  messages: string[];
};

function getAvatar(sender: 'self' | 'ai' | string) {
  const sharedStyles: SxProps<Theme> = {
    height: '2em',
    width: '2em'
  };

  switch (sender) {
    case 'self':
      return <Avatar src="" sx={{ ...sharedStyles }} />;
    case 'ai':
      return (
        <Avatar sx={{ ...sharedStyles }}>
          <PsychologyIcon />
        </Avatar>
      );
    default:
      return <Avatar src="?" sx={{ ...sharedStyles }} />;
  }
}

export function ChatMessages(props: ChatMessagesProps) {
  const theme = useTheme();
  const radius = theme.spacing(2);

  return (
    <Box sx={{ display: 'flex', ' > :not(:last-child)': { marginRight: 2 } }}>
      {getAvatar(props.sender)}
      <Box sx={{ flexGrow: 1, minWidth: 0 }}>
        {props.messages.map((message, i) => (
          // extra div needed to ensure each bubble is on a new line
          <Box key={i}>
            <Box
              sx={{
                display: 'inline-block',
                padding: theme.spacing(1, 2),
                borderRadius: radius,
                marginBottom: 1,
                wordBreak: 'break-word',
                textAlign: 'left',
                maxWidth: '100%',
                boxSizing: 'border-box',
                ...(props.sender === 'self'
                  ? {
                      backgroundColor: theme.palette.primary.main,
                      color: theme.palette.common.white
                    }
                  : {
                      backgroundColor: theme.palette.grey[100]
                    })
              }}
            >
              <ReactMarkdown
                components={{
                  code: ChatCodeView
                }}
                remarkPlugins={[remarkMath]}
                rehypePlugins={[rehypeKatex]}
              >
                {message}
              </ReactMarkdown>
            </Box>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
