import React, { useState, useEffect } from 'react';
import { Box } from '@mui/system';
import type { Awareness } from 'y-protocols/awareness';

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
import { CollaboratorsContextProvider } from '../contexts/collaborators-context';
import { ScrollContainer } from './scroll-container';

type ChatBodyProps = {
  chatHandler: ChatHandler;
};

function ChatBody({ chatHandler }: ChatBodyProps): JSX.Element {
  const [messages, setMessages] = useState<AiService.ChatMessage[]>([]);
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
      setMessages(history.messages);
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

      setMessages(messageGroups => [...messageGroups, message]);
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
      (includeSelection && selection?.text ? '\n\n```\n' + selection.text + '```': '');

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
        background: 'var(--jp-layout-color0)',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <ScrollContainer sx={{ flexGrow: 1 }}>
        <ChatMessages messages={messages} />
        {/* https://css-tricks.com/books/greatest-css-tricks/pin-scrolling-to-bottom/ */}
        <Box sx={{ overflowAnchor: 'auto', height: '1px' }} />
      </ScrollContainer>
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
          paddingLeft: 4,
          paddingRight: 4,
          paddingTop: 2,
          paddingBottom: 2,
          borderTop: '1px solid var(--jp-border-color1)'
        }}
      />
    </Box>
  );
}

export type ChatProps = {
  selectionWatcher: SelectionWatcher;
  chatHandler: ChatHandler;
  globalAwareness: Awareness | null;
};

export function Chat(props: ChatProps) {
  return (
    <JlThemeProvider>
      <SelectionContextProvider selectionWatcher={props.selectionWatcher}>
        <CollaboratorsContextProvider globalAwareness={props.globalAwareness}>
          <ChatBody chatHandler={props.chatHandler} />
        </CollaboratorsContextProvider>
      </SelectionContextProvider>
    </JlThemeProvider>
  );
}
