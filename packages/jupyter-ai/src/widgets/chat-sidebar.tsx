import React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';

import { Chat } from '../components/chat';
import { psychologyIcon } from '../icons';

export function buildChatSidebar() {
  const ChatWidget = ReactWidget.create(<Chat />);
  ChatWidget.id = 'jupyter-ai::chat';
  ChatWidget.title.icon = psychologyIcon;
  ChatWidget.title.caption = 'Jupyter AI Chat'; // TODO: i18n
  return ChatWidget;
}
