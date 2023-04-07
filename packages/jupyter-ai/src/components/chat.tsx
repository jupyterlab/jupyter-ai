import React, { useEffect, useState } from 'react';

import { Box } from '@mui/system';

import { JlThemeProvider } from './jl-theme-provider';
import { ChatMessages } from './chat-messages';
import { ChatInput } from './chat-input';

type ChatMessageGroup = {
  side: 'left' | 'right';
  messages: string[];
};

export function Chat(props: any): JSX.Element {
  const [messageGroups, setMessageGroups] = useState<ChatMessageGroup[]>([]);
  const [input, setInput] = useState('');

  function clearInput() {
    setInput('');
  }

  const onSend = async () => {
    clearInput();
    setMessageGroups(messageGroups => [
      ...messageGroups,
      { side: 'right', messages: [input] }
    ]);
    props.chatHandler.sendMessage(JSON.stringify({prompt: input}))
  };

  useEffect(() => {
    function handleChatEvents(message: any) {
      setMessageGroups(messageGroups => [
        ...messageGroups,
        { 
          side: message["type"] === "ai" ? 'left' : 'right', 
          messages: [message["data"]["content"]]}
      ])
    }

    props.chatHandler.getHistory().then((history: any) => {
      const messages = history['messages']
      if(messages.length > 0){
        const _messageGroups = messages.map((message: any): ChatMessageGroup => {
          return {
            side: message["type"] === "ai" ? 'left' : 'right',
            messages: [message["data"]["content"]]
          }
        });
        console.log("_messageGroups is ", _messageGroups);
        setMessageGroups(_messageGroups)
      }
    })
    
    props.chatHandler.addListener(handleChatEvents)

    return function cleanup() {
      props.chatHandler.removeListener(handleChatEvents)
    }

  }, []);


  return (
    <JlThemeProvider>
      <Box
        sx={{
          width: '100%',
          height: '100%',
          boxSizing: 'border-box',
          background: 'white',
          padding: 4,
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        <Box sx={{ flexGrow: 1, overflowY: "auto" }}>
          <ChatMessages side="right" messages={['Hello. Who are you?']} />
          <ChatMessages
            side="left"
            messages={[
              'My name is Jupyter AI, and I am a helpful assistant for Jupyter users.',
              'For example, I can write `python3` code like so:',
              '```py\nfor i in range(5):\n  print(i)\n```',
              'Would you like help with something?'
            ]}
          />
          {messageGroups.map((group, idx) => (
            <ChatMessages side={group.side} messages={group.messages} />
          ))}
        </Box>
        <ChatInput value={input} onChange={setInput} onSend={onSend} />
      </Box>
    </JlThemeProvider>
  );
}
