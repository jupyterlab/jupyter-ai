import React, { useState } from 'react';

import { Box } from '@mui/system';

import { JlThemeProvider } from './jl-theme-provider';
import { ChatMessages } from './chat-messages';
import { ChatInput } from './chat-input';
import { AiService } from '../handler';

type ChatMessageGroup = {
  sender: 'self' | 'ai' | string;
  messages: string[];
};

export function Chat(): JSX.Element {
  const [messageGroups, setMessageGroups] = useState<ChatMessageGroup[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [input, setInput] = useState('');

  const onSend = async () => {
    setLoading(true);
    setInput('');
    setMessageGroups(messageGroups => [
      ...messageGroups,
      { sender: 'self', messages: [input] }
    ]);

    let response: AiService.ChatResponse;

    try {
      response = await AiService.sendChat({ prompt: input });
    } finally {
      setLoading(false);
    }

    setMessageGroups(messageGroups => [
      ...messageGroups,
      { sender: 'ai', messages: [response.output] }
    ]);
  };

  return (
    <JlThemeProvider>
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
          <ChatMessages sender="self" messages={['Hello. Who are you?']} />
          <ChatMessages
            sender="ai"
            messages={[
              'My name is Jupyter AI, and I am a helpful assistant for Jupyter users.',
              'For example, I can write `python3` code like so:',
              '```py\nfor i in range(5):\n  print(i)\n```',
              'Would you like help with something?'
            ]}
          />
          <ChatMessages
            sender="self"
            messages={[
              'Could you show me an example implementation of a mutex lock in C++?'
            ]}
          />
          <ChatMessages
            sender="ai"
            messages={[
              'Certainly! Here\'s an example implementation of a mutex lock using C++ `pthread_mutex_t`:\n\n```cpp\n#include <iostream>\n#include <thread>\n#include <pthread.h>\n\n// Declare a mutex object\npthread_mutex_t myMutex;\n\nvoid printWithLock(const std::string& message) {\n    // Lock mutex before accessing shared resource\n    pthread_mutex_lock(&myMutex);\n\n    // Critical section (shared resource access)\n    std::cout << message << std::endl;\n\n    // Mutex is released upon calling pthread_mutex_unlock()\n    pthread_mutex_unlock(&myMutex);\n}\n\nvoid workerThread() {\n    for (int i = 0; i < 5; i++) {\n        printWithLock("Hello, World!");\n    }\n}\n\nint main() {\n    // Initialize the mutex object\n    pthread_mutex_init(&myMutex, NULL);\n\n    // Start worker thread\n    std::thread t(workerThread);\n\n    // Main thread\n    for (int i = 0; i < 5; i++) {\n        printWithLock("Hello, Mutex!");\n    }\n\n    // Wait for worker thread to finish\n    t.join();\n\n    // Destroy the mutex object\n    pthread_mutex_destroy(&myMutex);\n\n    return 0;\n}\n```\n\nIn this example implementation, we use the `pthread_mutex_t` data type to declare a mutex object called `myMutex`. In the `printWithLock` function, we call `pthread_mutex_lock()` to acquire the mutex lock before accessing the shared resource (`std::cout`). We then release the mutex lock by calling `pthread_mutex_unlock()` before exiting the function.\n\nWe also define a worker thread function `workerThread` that simply calls `printWithLock` five times with the message "Hello, World!". In the `main` function, we call `printWithLock` five times with the message "Hello, Mutex!" from the main thread and wait for the worker thread to finish by calling `t.join()`.\n\nWe initialize the mutex object using `pthread_mutex_init()` at the beginning of the `main` function and destroy it using `pthread_mutex_destroy()` before the end of the function.\n\nThis implementation ensures that only one thread at a time can access the shared resource, preventing race conditions and data corruption.'
            ]}
          />
          {messageGroups.map((group, idx) => (
            <ChatMessages sender={group.sender} messages={group.messages} />
          ))}
        </Box>
        <ChatInput
          loading={loading}
          value={input}
          onChange={setInput}
          onSend={onSend}
          sx={{
            padding: 2
          }}
        />
      </Box>
    </JlThemeProvider>
  );
}
