import React, { useState } from 'react';

import { Box } from '@mui/system';

import { JlThemeProvider } from './jl-theme-provider';
import { ChatMessages } from './chat-messages';
import { ChatInput } from './chat-input';
//import { AiService } from '../handler';

type ChatMessageGroup = {
  side: 'left' | 'right';
  messages: string[];
};

export function Chat(props: any): JSX.Element {
  const [messageGroups, setMessageGroups] = useState<ChatMessageGroup[]>([]);
  const [input, setInput] = useState('');

  const onSend = async () => {
    setInput('');
    setMessageGroups(messageGroups => [
      ...messageGroups,
      { side: 'right', messages: [input] }
    ]);
    /*const response = await AiService.sendChat({ prompt: input });
    setMessageGroups(messageGroups => [
      ...messageGroups,
      { side: 'left', messages: [response.output] }
    ]);*/
    props.chatHandler.sendMessage(JSON.stringify({prompt: input}))
    props.chatHandler.addListener((event: any) => {
      if(event["event"] == "reply") {
        setMessageGroups(messageGroups => [
          ...messageGroups,
          { side: 'left', messages: [event["data"]]}
        ])
      }
      // TODO: add for history event
      
    });
  };

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
        <Box sx={{ flexGrow: 1 }}>
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
