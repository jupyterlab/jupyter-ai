import React, { useState, useEffect } from 'react';
import { Box } from '@mui/system';
import { Button, IconButton, Stack } from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AddIcon from '@mui/icons-material/Add';
import type { Awareness } from 'y-protocols/awareness';
import type { IThemeManager } from '@jupyterlab/apputils';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import type { User } from '@jupyterlab/services';
import { ISignal } from '@lumino/signaling';

import { JlThemeProvider } from './jl-theme-provider';
import { ChatMessages } from './chat-messages';
import { PendingMessages } from './pending-messages';
import { ChatInput } from './chat-input';
import { ChatSettings } from './chat-settings';
import { AiService } from '../handler';
import { SelectionContextProvider } from '../contexts/selection-context';
import { SelectionWatcher } from '../selection-watcher';
import { ChatHandler } from '../chat_handler';
import { CollaboratorsContextProvider } from '../contexts/collaborators-context';
import {
  IJaiCompletionProvider,
  IJaiMessageFooter,
  IJaiTelemetryHandler
} from '../tokens';
import {
  ActiveCellContextProvider,
  ActiveCellManager
} from '../contexts/active-cell-context';
import { UserContextProvider, useUserContext } from '../contexts/user-context';
import { ScrollContainer } from './scroll-container';
import { TooltippedIconButton } from './mui-extras/tooltipped-icon-button';
import { TelemetryContextProvider } from '../contexts/telemetry-context';

type ChatBodyProps = {
  chatHandler: ChatHandler;
  openSettingsView: () => void;
  showWelcomeMessage: boolean;
  setShowWelcomeMessage: (show: boolean) => void;
  rmRegistry: IRenderMimeRegistry;
  focusInputSignal: ISignal<unknown, void>;
  messageFooter: IJaiMessageFooter | null;
};

/**
 * Determines the name of the current persona based on the message history.
 * Defaults to `'Jupyternaut'` if history is insufficient.
 */
function getPersonaName(messages: AiService.ChatMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const message = messages[i];
    if (message.type === 'agent' || message.type === 'agent-stream') {
      return message.persona.name;
    }
  }

  return 'Jupyternaut';
}

function ChatBody({
  chatHandler,
  focusInputSignal,
  openSettingsView,
  showWelcomeMessage,
  setShowWelcomeMessage,
  rmRegistry: renderMimeRegistry,
  messageFooter
}: ChatBodyProps): JSX.Element {
  const [messages, setMessages] = useState<AiService.ChatMessage[]>([
    ...chatHandler.history.messages
  ]);
  const [pendingMessages, setPendingMessages] = useState<
    AiService.PendingMessage[]
  >([...chatHandler.history.pending_messages]);
  const [personaName, setPersonaName] = useState<string>(
    getPersonaName(messages)
  );
  const [sendWithShiftEnter, setSendWithShiftEnter] = useState(true);
  const user = useUserContext();

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
      setPersonaName(getPersonaName(history.messages));
    }

    chatHandler.historyChanged.connect(onHistoryChange);

    return function cleanup() {
      chatHandler.historyChanged.disconnect(onHistoryChange);
    };
  }, [chatHandler]);

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

  // set of IDs of messages sent by the current user.
  const myHumanMessageIds = new Set(
    messages
      .filter(
        m => m.type === 'human' && m.client.username === user?.identity.username
      )
      .map(m => m.id)
  );

  // whether the backend is currently streaming a reply to any message sent by
  // the current user.
  const streamingReplyHere = messages.some(
    m =>
      m.type === 'agent-stream' &&
      myHumanMessageIds.has(m.reply_to) &&
      !m.complete
  );

  return (
    <>
      <ScrollContainer sx={{ flexGrow: 1 }}>
        <ChatMessages
          messages={messages}
          chatHandler={chatHandler}
          rmRegistry={renderMimeRegistry}
          messageFooter={messageFooter}
        />
        <PendingMessages messages={pendingMessages} chatHandler={chatHandler} />
      </ScrollContainer>
      <ChatInput
        chatHandler={chatHandler}
        focusInputSignal={focusInputSignal}
        streamingReplyHere={streamingReplyHere}
        sx={{
          paddingLeft: 4,
          paddingRight: 4,
          paddingTop: 3.5,
          paddingBottom: 0,
          borderTop: '1px solid var(--jp-border-color1)'
        }}
        sendWithShiftEnter={sendWithShiftEnter}
        personaName={personaName}
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
  messageFooter: IJaiMessageFooter | null;
  telemetryHandler: IJaiTelemetryHandler | null;
  userManager: User.IManager;
};

enum ChatView {
  Chat,
  Settings
}

export function Chat(props: ChatProps): JSX.Element {
  const [view, setView] = useState<ChatView>(props.chatView || ChatView.Chat);
  const [showWelcomeMessage, setShowWelcomeMessage] = useState<boolean>(false);

  const openSettingsView = () => {
    setShowWelcomeMessage(false);
    setView(ChatView.Settings);
  };

  return (
    <JlThemeProvider themeManager={props.themeManager}>
      <SelectionContextProvider selectionWatcher={props.selectionWatcher}>
        <CollaboratorsContextProvider globalAwareness={props.globalAwareness}>
          <ActiveCellContextProvider
            activeCellManager={props.activeCellManager}
          >
            <TelemetryContextProvider telemetryHandler={props.telemetryHandler}>
              <UserContextProvider userManager={props.userManager}>
                <Box
                  // Add .jp-ThemedContainer for CSS compatibility in both JL <4.3.0 and >=4.3.0.
                  // See: https://jupyterlab.readthedocs.io/en/latest/extension/extension_migration.html#css-styling
                  className="jp-ThemedContainer"
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
                  <Box
                    sx={{ display: 'flex', justifyContent: 'space-between' }}
                  >
                    {view !== ChatView.Chat ? (
                      <IconButton onClick={() => setView(ChatView.Chat)}>
                        <ArrowBackIcon />
                      </IconButton>
                    ) : (
                      <Box />
                    )}
                    {view === ChatView.Chat ? (
                      <Box sx={{ display: 'flex' }}>
                        {!showWelcomeMessage && (
                          <TooltippedIconButton
                            onClick={() =>
                              props.chatHandler.sendMessage({ type: 'clear' })
                            }
                            tooltip="New chat"
                          >
                            <AddIcon />
                          </TooltippedIconButton>
                        )}
                        <IconButton onClick={() => openSettingsView()}>
                          <SettingsIcon />
                        </IconButton>
                      </Box>
                    ) : (
                      <Box />
                    )}
                  </Box>
                  {/* body */}
                  {view === ChatView.Chat && (
                    <ChatBody
                      chatHandler={props.chatHandler}
                      openSettingsView={openSettingsView}
                      showWelcomeMessage={showWelcomeMessage}
                      setShowWelcomeMessage={setShowWelcomeMessage}
                      rmRegistry={props.rmRegistry}
                      focusInputSignal={props.focusInputSignal}
                      messageFooter={props.messageFooter}
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
              </UserContextProvider>
            </TelemetryContextProvider>
          </ActiveCellContextProvider>
        </CollaboratorsContextProvider>
      </SelectionContextProvider>
    </JlThemeProvider>
  );
}
