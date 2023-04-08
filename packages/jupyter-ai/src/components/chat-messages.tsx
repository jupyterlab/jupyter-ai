import React from 'react';

import { Avatar, Box, Grid, useTheme } from '@mui/material';
import ReactMarkdown from 'react-markdown';

import { ChatCodeView } from './chat-code-view';

type ChatMessagesProps = {
  side: 'left' | 'right';
  messages: string[];
};

export function ChatMessages(props: ChatMessagesProps) {
  const theme = useTheme();
  const radius = theme.spacing(2);

  return (
    <Grid
      container
      spacing={2}
      justifyContent={props.side === 'right' ? 'flex-end' : 'flex-start'}
    >
      {props.side === 'left' && (
        <Grid item>
          <Avatar src={''} />
        </Grid>
      )}
      <Grid item xs={8} sx={{ textAlign: props.side }}>
        {props.messages.map((message, i) => (
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
                ...(props.side === 'left'
                  ? {
                      borderTopRightRadius: radius,
                      borderBottomRightRadius: radius,
                      backgroundColor: theme.palette.grey[100]
                    }
                  : {
                      borderTopLeftRadius: radius,
                      borderBottomLeftRadius: radius,
                      backgroundColor: theme.palette.primary.main,
                      color: theme.palette.common.white
                    }),
                ...(props.side === 'left' &&
                  i === 0 && {
                    borderTopLeftRadius: radius
                  }),
                ...(props.side === 'left' &&
                  i === props.messages.length - 1 && {
                    borderBottomLeftRadius: radius
                  }),
                ...(props.side === 'right' &&
                  i === 0 && {
                    borderTopRightRadius: radius
                  }),
                ...(props.side === 'right' &&
                  i === props.messages.length - 1 && {
                    borderBottomRightRadius: radius
                  })
              }}
            >
              <ReactMarkdown
                components={{
                  code: ChatCodeView
                }}
              >
                {message}
              </ReactMarkdown>
            </Box>
          </Box>
        ))}
      </Grid>
    </Grid>
  );
}
