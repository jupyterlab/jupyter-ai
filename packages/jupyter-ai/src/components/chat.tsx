import React, {
  useState
  // useMemo,
  // useEffect
} from 'react';

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
// import { ChatHandler } from '../chat_handler';

type ChatMessageGroup = {
  sender: 'self' | 'ai' | string;
  messages: string[];
};

function ChatBody(): JSX.Element {
  const [messageGroups, setMessageGroups] = useState<ChatMessageGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [includeSelection, setIncludeSelection] = useState(true);
  const [replaceSelection, setReplaceSelection] = useState(false);
  const [input, setInput] = useState('');
  const [selection, replaceSelectionFn] = useSelectionContext();

  // TODO: connect to websockets.
  // const chatHandler = useMemo(() => new ChatHandler(), []);
  //
  // /**
  //  * Effect: fetch history on initial render
  //  */
  // useEffect(() => {
  //   async function fetchHistory() {
  //     const history = await chatHandler.getHistory();
  //     const messages = history.messages;
  //     if (!messages.length) {
  //       return;
  //     }

  //     const newMessageGroups = messages.map(
  //       (message: AiService.ChatMessage): ChatMessageGroup => ({
  //         sender: message.type === 'ai' ? 'ai' : 'self',
  //         messages: [message.data.content]
  //       })
  //     );
  //     setMessageGroups(newMessageGroups);
  //   }

  //   fetchHistory();
  // }, [chatHandler]);

  // /**
  //  * Effect: listen to chat messages
  //  */
  // useEffect(() => {
  //   function handleChatEvents(message: AiService.ChatMessage) {
  //     setMessageGroups(messageGroups => [
  //       ...messageGroups,
  //       {
  //         sender: message.type === 'ai' ? 'ai' : 'self',
  //         messages: [message.data.content]
  //       }
  //     ]);
  //   }

  //   chatHandler.addListener(handleChatEvents);

  //   return function cleanup() {
  //     chatHandler.removeListener(handleChatEvents);
  //   };
  // }, [chatHandler]);

  const onSend = async () => {
    setLoading(true);
    setInput('');
    console.log({
      includeSelection,
      replaceSelection
    });
    const newMessages = [input];
    if (includeSelection && selection) {
      newMessages.push('```\n' + selection + '\n```');
    }
    setMessageGroups(messageGroups => [
      ...messageGroups,
      { sender: 'self', messages: newMessages }
    ]);

    let response: AiService.ChatResponse;

    const prompt = input + (selection ? '\n--\n' + selection : '');
    try {
      response = await AiService.sendChat({ prompt });
    } finally {
      setLoading(false);
    }

    if (replaceSelection) {
      replaceSelectionFn(response.output);
    }
    setMessageGroups(messageGroups => [
      ...messageGroups,
      { sender: 'ai', messages: [response.output] }
    ]);
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
        loading={loading}
        value={input}
        onChange={setInput}
        onSend={onSend}
        hasSelection={!!selection}
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
};

export function Chat(props: ChatProps) {
  return (
    <JlThemeProvider>
      <SelectionContextProvider selectionWatcher={props.selectionWatcher}>
        <ChatBody />
      </SelectionContextProvider>
    </JlThemeProvider>
  );
}
