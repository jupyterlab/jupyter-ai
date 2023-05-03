import React, { useState, useEffect } from 'react';
import { Box } from '@mui/system';
import { IconButton } from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import type { Awareness } from 'y-protocols/awareness';

import { JlThemeProvider } from './jl-theme-provider';
import { ChatMessages } from './chat-messages';
import { ChatInput } from './chat-input';
import { ChatSettings } from './chat-settings';
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
  const [showWelcomeMessage, setShowWelcomeMessage] = useState<boolean>(false);
  const [includeSelection, setIncludeSelection] = useState(true);
  const [replaceSelection, setReplaceSelection] = useState(false);
  const [input, setInput] = useState('');
  const [selection, replaceSelectionFn] = useSelectionContext();

  /**
   * Effect: fetch history on initial render
   */
  useEffect(() => {
    async function fetchHistory() {
      try {
        const [history, config] = await Promise.all([
          chatHandler.getHistory(),
          AiService.getConfig()
        ]);
        setMessages(history.messages);
        if (!config.model_provider_id) {
          setShowWelcomeMessage(true);
        }
      } catch (e) {
        console.error(e);
      }
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
      } else if (message.type === 'clear') {
        setMessages([]);
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
      (includeSelection && selection?.text
        ? '\n\n```\n' + selection.text + '```'
        : '');

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

  if (showWelcomeMessage) {
    return (
      <Box
        sx={{
          padding: 4,
          display: 'flex',
          flexGrow: 1,
          alignItems: 'center',
          justifyContent: 'space-around'
        }}
      >
        Welcome to Jupyter AI! To get started, please select a language model to
        chat with from the settings menu at the top right. You will also likely
        need to provide API credentials, so be sure to have those handy.
      </Box>
    );
  }

  return (
    <>
      <ScrollContainer sx={{ flexGrow: 1 }}>
        <ChatMessages messages={messages} />
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
          paddingTop: 3.5,
          paddingBottom: 0,
          borderTop: '1px solid var(--jp-border-color1)'
        }}
        helperText={
          <span>
            <b>Press Shift</b> + <b>Enter</b> to submit message
          </span>
        }
      />
    </>
  );
}

export type ChatProps = {
  selectionWatcher: SelectionWatcher;
  chatHandler: ChatHandler;
  globalAwareness: Awareness | null;
};

enum ChatView {
  Chat,
  Settings
}

export function Chat(props: ChatProps) {
  const [view, setView] = useState<ChatView>(ChatView.Chat);

  return (
    <JlThemeProvider>
      <SelectionContextProvider selectionWatcher={props.selectionWatcher}>
        <CollaboratorsContextProvider globalAwareness={props.globalAwareness}>
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
            {/* top bar */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              {view !== ChatView.Chat ? (
                <IconButton onClick={() => setView(ChatView.Chat)}>
                  <ArrowBackIcon />
                </IconButton>
              ) : (
                <Box />
              )}
              {view === ChatView.Chat ? (
                <IconButton onClick={() => setView(ChatView.Settings)}>
                  <SettingsIcon />
                </IconButton>
              ) : (
                <Box />
              )}
            </Box>
            {/* body */}
            {view === ChatView.Chat && (
              <ChatBody chatHandler={props.chatHandler} />
            )}
            {view === ChatView.Settings && <ChatSettings />}
          </Box>
        </CollaboratorsContextProvider>
      </SelectionContextProvider>
    </JlThemeProvider>
  );
}
