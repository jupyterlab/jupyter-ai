import React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';

import { Chat } from '../components/chat';
import { psychologyIcon } from '../icons';
import { SelectionWatcher } from '../selection-watcher';

export function buildChatSidebar(selectionWatcher: SelectionWatcher) {
  const ChatWidget = ReactWidget.create(
    <Chat selectionWatcher={selectionWatcher} />
  );
  ChatWidget.id = 'jupyter-ai::chat';
  ChatWidget.title.icon = psychologyIcon;
  ChatWidget.title.caption = 'Jupyter AI Chat'; // TODO: i18n
  return ChatWidget;
}
