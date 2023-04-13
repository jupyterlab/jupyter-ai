import React, { useState, useEffect } from 'react';

import { Box } from '@mui/system';

import { JlThemeProvider } from './jl-theme-provider';
import { ChatMessages } from './chat-messages';
import { ChatInput } from './chat-input';
import { AiService } from '../handler';
import {
  SelectionContextProvider,
  useSelectionContext
} from '../contexts/selection-context';
import { SelectionWatcher } from '../selection-watcher';
import { ChatHandler } from '../chat_handler';

type ChatMessageGroup = {
  sender: 'self' | 'ai' | string;
  messages: string[];
};

type ChatBodyProps = {
  chatHandler: ChatHandler;
};

function ChatBody({ chatHandler }: ChatBodyProps): JSX.Element {
  const [messageGroups, setMessageGroups] = useState<ChatMessageGroup[]>([]);
  const [includeSelection, setIncludeSelection] = useState(true);
  const [replaceSelection, setReplaceSelection] = useState(false);
  const [input, setInput] = useState('');
  const [selection, replaceSelectionFn] = useSelectionContext();

  /**
   * Effect: fetch history on initial render
   */
  useEffect(() => {
    async function fetchHistory() {
      const history = await chatHandler.getHistory();
      const messages = history.messages;
      if (!messages.length) {
        return;
      }

      const newMessageGroups = messages.map(
        (message: AiService.ChatMessage): ChatMessageGroup => ({
          sender: message.type === 'agent' ? 'ai' : 'self',
          messages: [message.body]
        })
      );
      setMessageGroups(newMessageGroups);
    }

    fetchHistory();
  }, [chatHandler]);

  /**
   * Effect: listen to chat messages
   */
  useEffect(() => {
    function handleChatEvents(message: AiService.Message) {
      if (message.type === 'connection') {
        return;
      }

      setMessageGroups(messageGroups => [
        ...messageGroups,
        {
          sender: message.type === 'agent' ? 'ai' : 'self',
          messages: [message.body]
        }
      ]);
    }

    chatHandler.addListener(handleChatEvents);
    return function cleanup() {
      chatHandler.removeListener(handleChatEvents);
    };
  }, [chatHandler]);

  // no need to append to messageGroups imperatively here. all of that is
  // handled by the listeners registered in the effect hooks above.
  const onSend = async () => {
    setInput('');

    const prompt =
      input +
      (includeSelection && selection?.text ? '\n--\n' + selection.text : '');

    // send message to backend
    const messageId = await chatHandler.sendMessage({ prompt });

    // await reply from agent
    // no need to append to messageGroups state variable, since that's already
    // handled in the effect hooks.
    const reply = await chatHandler.replyFor(messageId);
    if (replaceSelection && selection) {
      const { cellId, ...selectionProps } = selection;
      replaceSelectionFn({
        ...selectionProps,
        ...(cellId && { cellId }),
        text: reply.body
      });
    }
  };

  return (
    <Box
      // root box should not include padding as it offsets the vertical
      // scrollbar to the left
      sx={{
        width: '100%',
        height: '100%',
        boxSizing: 'border-box',
        background: 'white',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <Box
        sx={{
          flexGrow: 1,
          padding: 2,
          overflowY: 'scroll',
          '> :not(:last-child)': {
            marginBottom: 1
          }
        }}
      >
        {messageGroups.map((group, idx) => (
          <ChatMessages
            key={idx}
            sender={group.sender}
            messages={group.messages}
          />
        ))}
      </Box>
      <ChatInput
        value={input}
        onChange={setInput}
        onSend={onSend}
        hasSelection={!!selection?.text}
        includeSelection={includeSelection}
        toggleIncludeSelection={() =>
          setIncludeSelection(includeSelection => !includeSelection)
        }
        replaceSelection={replaceSelection}
        toggleReplaceSelection={() =>
          setReplaceSelection(replaceSelection => !replaceSelection)
        }
        sx={{
          padding: 2
        }}
      />
    </Box>
  );
}

export type ChatProps = {
  selectionWatcher: SelectionWatcher;
  chatHandler: ChatHandler;
};

export function Chat(props: ChatProps) {
  return (
    <JlThemeProvider>
      <SelectionContextProvider selectionWatcher={props.selectionWatcher}>
        <ChatBody chatHandler={props.chatHandler} />
      </SelectionContextProvider>
    </JlThemeProvider>
  );
}
