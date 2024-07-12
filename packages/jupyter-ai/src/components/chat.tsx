import React, { useState, useEffect } from 'react';
import { Box } from '@mui/system';
import { Button, IconButton, Stack } from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import type { Awareness } from 'y-protocols/awareness';
import type { IThemeManager } from '@jupyterlab/apputils';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { ISignal } from '@lumino/signaling';

import { JlThemeProvider } from './jl-theme-provider';
import { ChatMessages } from './chat-messages';
import { PendingMessages } from './pending-messages';
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
import { IJaiCompletionProvider } from '../tokens';
import {
  ActiveCellContextProvider,
  ActiveCellManager
} from '../contexts/active-cell-context';
import { ScrollContainer } from './scroll-container';

type ChatBodyProps = {
  chatHandler: ChatHandler;
  setChatView: (view: ChatView) => void;
  rmRegistry: IRenderMimeRegistry;
  focusInputSignal: ISignal<unknown, void>;
};

function ChatBody({
  chatHandler,
  focusInputSignal,
  setChatView: chatViewHandler,
  rmRegistry: renderMimeRegistry
}: ChatBodyProps): JSX.Element {
  const [messages, setMessages] = useState<AiService.ChatMessage[]>([
    ...chatHandler.history.messages
  ]);
  const [pendingMessages, setPendingMessages] = useState<
    AiService.PendingMessage[]
  >([...chatHandler.history.pending_messages]);
  const [showWelcomeMessage, setShowWelcomeMessage] = useState<boolean>(false);
  const [includeSelection, setIncludeSelection] = useState(true);
  const [input, setInput] = useState('');
  const [textSelection] = useSelectionContext();
  const [sendWithShiftEnter, setSendWithShiftEnter] = useState(true);

  /**
   * Effect: fetch config on initial render
   */
  useEffect(() => {
    async function fetchConfig() {
      try {
        const config = await AiService.getConfig();
        setSendWithShiftEnter(config.send_with_shift_enter ?? false);
        if (!config.model_provider_id) {
          setShowWelcomeMessage(true);
        }
      } catch (e) {
        console.error(e);
      }
    }

    fetchConfig();
  }, [chatHandler]);

  /**
   * Effect: listen to chat messages
   */
  useEffect(() => {
    function onHistoryChange(_: unknown, history: AiService.ChatHistory) {
      setMessages([...history.messages]);
      setPendingMessages([...history.pending_messages]);
    }

    chatHandler.historyChanged.connect(onHistoryChange);

    return function cleanup() {
      chatHandler.historyChanged.disconnect(onHistoryChange);
    };
  }, [chatHandler]);

  // no need to append to messageGroups imperatively here. all of that is
  // handled by the listeners registered in the effect hooks above.
  // TODO: unify how text selection & cell selection are handled
  const onSend = async (selection?: AiService.Selection) => {
    setInput('');

    const prompt =
      input +
      (includeSelection && textSelection?.text
        ? '\n\n```\n' + textSelection.text + '\n```'
        : '');

    // send message to backend
    const messageId = await chatHandler.sendMessage({ prompt, selection });

    // await reply from agent
    await chatHandler.replyFor(messageId);
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
        <ChatMessages messages={messages} rmRegistry={renderMimeRegistry} />
        <PendingMessages messages={pendingMessages} />
      </ScrollContainer>
      <ChatInput
        value={input}
        onChange={setInput}
        onSend={onSend}
        hasSelection={!!textSelection?.text}
        includeSelection={includeSelection}
        focusInputSignal={focusInputSignal}
        toggleIncludeSelection={() =>
          setIncludeSelection(includeSelection => !includeSelection)
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
  chatHandler: ChatHandler;
  globalAwareness: Awareness | null;
  themeManager: IThemeManager | null;
  rmRegistry: IRenderMimeRegistry;
  chatView?: ChatView;
  completionProvider: IJaiCompletionProvider | null;
  openInlineCompleterSettings: () => void;
  activeCellManager: ActiveCellManager;
  focusInputSignal: ISignal<unknown, void>;
};

enum ChatView {
  Chat,
  Settings
}

export function Chat(props: ChatProps): JSX.Element {
  const [view, setView] = useState<ChatView>(props.chatView || ChatView.Chat);

  return (
    <JlThemeProvider themeManager={props.themeManager}>
      <SelectionContextProvider selectionWatcher={props.selectionWatcher}>
        <CollaboratorsContextProvider globalAwareness={props.globalAwareness}>
          <ActiveCellContextProvider
            activeCellManager={props.activeCellManager}
          >
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
                <ChatBody
                  chatHandler={props.chatHandler}
                  setChatView={setView}
                  rmRegistry={props.rmRegistry}
                  focusInputSignal={props.focusInputSignal}
                />
              )}
              {view === ChatView.Settings && (
                <ChatSettings
                  rmRegistry={props.rmRegistry}
                  completionProvider={props.completionProvider}
                  openInlineCompleterSettings={
                    props.openInlineCompleterSettings
                  }
                />
              )}
            </Box>
          </ActiveCellContextProvider>
        </CollaboratorsContextProvider>
      </SelectionContextProvider>
    </JlThemeProvider>
  );
}
