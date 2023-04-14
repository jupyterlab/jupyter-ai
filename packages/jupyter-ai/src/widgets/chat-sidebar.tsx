import React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import type { Awareness } from 'y-protocols/awareness';

import { Chat } from '../components/chat';
import { psychologyIcon } from '../icons';
import { SelectionWatcher } from '../selection-watcher';
import { ChatHandler } from '../chat_handler';

export function buildChatSidebar(
  selectionWatcher: SelectionWatcher,
  chatHandler: ChatHandler,
  globalAwareness: Awareness | null
) {
  const ChatWidget = ReactWidget.create(
    <Chat
      selectionWatcher={selectionWatcher}
      chatHandler={chatHandler}
      globalAwareness={globalAwareness}
    />
  );
  ChatWidget.id = 'jupyter-ai::chat';
  ChatWidget.title.icon = psychologyIcon;
  ChatWidget.title.caption = 'Jupyter AI Chat'; // TODO: i18n
  return ChatWidget;
}
