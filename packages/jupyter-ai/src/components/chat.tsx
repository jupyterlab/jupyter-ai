import React, { useState, useEffect } from 'react';
import { Box } from '@mui/system';
import { Alert, AlertTitle, Button, IconButton, Stack } from '@mui/material';
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
  chatHandler: ChatHandler | null;
  setChatView: (view: ChatView) => void;
};

function ChatBody({
  chatHandler,
  setChatView: chatViewHandler
}: ChatBodyProps): JSX.Element {
  const [messages, setMessages] = useState<AiService.ChatMessage[]>([]);
  const [showWelcomeMessage, setShowWelcomeMessage] = useState<boolean>(false);
  const [includeSelection, setIncludeSelection] = useState(true);
  const [replaceSelection, setReplaceSelection] = useState(false);
  const [input, setInput] = useState('');
  const [selection, replaceSelectionFn] = useSelectionContext();
  const [sendWithShiftEnter, setSendWithShiftEnter] = useState(true);
  const [configErrors, setConfigErrors] = useState<AiService.ConfigError[]>([]);

  /**
   * Effect: fetch history and config on initial render
   */
  useEffect(() => {
    async function fetchHistory() {
      try {
        const config = await AiService.getConfig();
        setSendWithShiftEnter(config.send_with_shift_enter ?? false);

        // Check if there are critical errors
        const hasCriticalErrors = config.config_errors?.some(
          error => error.error_type === AiService.ConfigErrorType.CRITICAL
        );
        console.log('\n\n\n *** \n\n\n');
        console.log(hasCriticalErrors);
        if (!hasCriticalErrors && chatHandler) {
          const history = await chatHandler.getHistory();
          setMessages(history.messages);
        } else {
          setMessages([]);
        }

        if (!config.model_provider_id) {
          setShowWelcomeMessage(true);
        }
        if (config.config_errors) {
          setConfigErrors(config.config_errors);
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

    chatHandler?.addListener(handleChatEvents);
    return function cleanup() {
      chatHandler?.removeListener(handleChatEvents);
    };
  }, [chatHandler]);

  // no need to append to messageGroups imperatively here. all of that is
  // handled by the listeners registered in the effect hooks above.
  const onSend = async () => {
    setInput('');

    const prompt =
      input +
      (includeSelection && selection?.text
        ? '\n\n```\n' + selection.text + '\n```'
        : '');

    // send message to backend
    const messageId = await chatHandler?.sendMessage({ prompt });

    // await reply from agent
    // no need to append to messageGroups state variable, since that's already
    // handled in the effect hooks.
    const reply = await chatHandler?.replyFor(messageId ?? '');
    if (replaceSelection && selection) {
      const { cellId, ...selectionProps } = selection;
      replaceSelectionFn({
        ...selectionProps,
        ...(cellId && { cellId }),
        text: reply?.body ?? ''
      });
    }
  };

  const openSettingsView = () => {
    setShowWelcomeMessage(false);
    chatViewHandler(ChatView.Settings);
  };

  if (showWelcomeMessage) {
    return (
      <Box
        sx={{
          padding: 4,
          display: 'flex',
          flexGrow: 1,
          alignItems: 'top',
          justifyContent: 'space-around'
        }}
      >
        <Stack spacing={4}>
          {configErrors &&
            configErrors.map((error, idx) => (
              <Alert key={idx} severity="warning">
                <AlertTitle>{error.error_type}</AlertTitle>
                {error.message} {error.details && `- ${error.details}`}
              </Alert>
            ))}
          <p className="jp-ai-ChatSettings-welcome">
            Welcome to Jupyter AI! To get started, please select a language
            model to chat with from the settings panel. You may also need to
            provide API credentials, so have those handy.
          </p>
          <Button
            variant="contained"
            startIcon={<SettingsIcon />}
            size={'large'}
            onClick={() => openSettingsView()}
          >
            Start Here
          </Button>
        </Stack>
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
        sendWithShiftEnter={sendWithShiftEnter}
      />
    </>
  );
}

export type ChatProps = {
  selectionWatcher: SelectionWatcher;
  chatHandler: ChatHandler | null;
  globalAwareness: Awareness | null;
  chatView?: ChatView;
};

enum ChatView {
  Chat,
  Settings
}

export function Chat(props: ChatProps): JSX.Element {
  const [view, setView] = useState<ChatView>(props.chatView || ChatView.Chat);

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
              <ChatBody chatHandler={props.chatHandler} setChatView={setView} />
            )}
            {view === ChatView.Settings && <ChatSettings />}
          </Box>
        </CollaboratorsContextProvider>
      </SelectionContextProvider>
    </JlThemeProvider>
  );
}
