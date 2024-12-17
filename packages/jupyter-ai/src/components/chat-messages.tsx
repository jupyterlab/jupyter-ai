import React, { useState, useEffect } from 'react';
import { Avatar, Box, IconButton, Paper, Typography } from '@mui/material';
import type { SxProps, Theme } from '@mui/material';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { ServerConnection } from '@jupyterlab/services';
// TODO: delete jupyternaut from frontend package
import CheckIcon from '@mui/icons-material/Check';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { AiService } from '../handler';
import { RendermimeMarkdown } from './rendermime-markdown';
import { useCollaboratorsContext } from '../contexts/collaborators-context';
import { ChatMessageMenu } from './chat-messages/chat-message-menu';
import { ChatHandler } from '../chat_handler';
import { IJaiMessageFooter } from '../tokens';
import { ChevronRight, ExpandMore } from '@mui/icons-material';
import { CopyStatus, useCopy } from '../hooks/use-copy';

type ChatMessagesProps = {
  rmRegistry: IRenderMimeRegistry;
  messages: AiService.ChatMessage[];
  chatHandler: ChatHandler;
  messageFooter: IJaiMessageFooter | null;
};

type ChatMessageHeaderProps = {
  message: AiService.ChatMessage;
  chatHandler: ChatHandler;
  timestamp: string;
  sx?: SxProps<Theme>;
  onFullPromptChange?: () => void;
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
      'reply_to' in a && a.reply_to in timestampsById
        ? timestampsById[a.reply_to]
        : a.time;
    const bOriginTimestamp =
      'reply_to' in b && b.reply_to in timestampsById
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
        <Box sx={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Typography
            sx={{
              fontSize: '0.8em',
              color: 'var(--jp-ui-font-color2)',
              fontWeight: 300
            }}
          >
            {props.timestamp}
          </Typography>
            <ChatMessageMenu
              message={props.message}
              chatHandler={props.chatHandler}
            />
        </Box>
      </Box>
    </Box>
  );
}

interface ChatMessageProps {
    message: AiService.ChatMessage;
    timestamp: string;
    chatHandler: ChatHandler;
    rmRegistry: IRenderMimeRegistry;
    messageFooter?: IJaiMessageFooter | null;
}

const ChatMessage = ({
    message,
    timestamp,
    chatHandler,
    rmRegistry,
    messageFooter
}: ChatMessageProps) => {
    const [showFullPrompt, setShowFullPrompt] = useState(false);
    const {
        copy: copyText,
        copyStatus
    } = useCopy();

    const CopyStatusIcon = copyStatus === CopyStatus.Copied ? CheckIcon : ContentCopyIcon;

    return (
        <Box key={message.id} sx={{ padding: 4 }}>
            <ChatMessageHeader
                message={message}
                timestamp={timestamp}
                chatHandler={chatHandler}
                sx={{ marginBottom: 3 }}
            />
            {message.type === 'agent-stream' && message.metadata?.prompt && <Box display="flex" flexGrow={1} gap={2} alignItems="flex-start"  marginBottom={1}>
                <Box marginTop={0.5} sx={{cursor: "pointer"}} onClick={() => setShowFullPrompt(x => !x)}>
                    {showFullPrompt ? <ExpandMore fontSize="small" /> : <ChevronRight fontSize="small" />}
                </Box>
                <Box sx={{cursor: "pointer"}} width="95%">
                    <Box display="flex" flexDirection="row" gap={1} alignItems="flex-start">
                        <Typography
                            sx={{
                                color: 'var(--jp-ui-font-color2)',
                            }}
                            onClick={() => setShowFullPrompt(x => !x)}
                        >
                            {showFullPrompt ? "Hide" : "View"} Prompt
                        </Typography>
                        <IconButton onClick={() => copyText(message.metadata?.prompt)}>
                            <CopyStatusIcon fontSize="inherit" />
                        </IconButton>
                    </Box>
                    {
                        showFullPrompt && (
                            <Paper sx={{ maxHeight: "300px", overflow: "auto", padding: 2, marginVertical: 1 }}>
                                <RendermimeMarkdown
                                    rmRegistry={rmRegistry}
                                    markdownStr={`\`\`\`${message.metadata?.prompt}`}
                                    complete={
                                        message.type === 'agent-stream' ? !!message.complete : true
                                    }
                                    hideCodeToolbar
                                />
                            </Paper>
                        )
                }
                </Box>
            </Box>}
            <RendermimeMarkdown
                rmRegistry={rmRegistry}
                markdownStr={message.body}
                complete={
                    message.type === 'agent-stream' ? !!message.complete : true
                }
            />
            {messageFooter && (
                <messageFooter.component message={message} />
            )}
        </Box>
    )
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
        return (
            <ChatMessage
                message={message}
                timestamp={timestamps[message.id]}
                rmRegistry={props.rmRegistry}
                messageFooter={props.messageFooter}
                chatHandler={props.chatHandler}
            />
        );
      })}
    </Box>
  );
}
