import React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';

import { Chat } from '../components/chat';
import { psychologyIcon } from '../icons';
import { ChatHandler } from '../chat_handler';

export function buildChatSidebar() {
  const chatHandler = new ChatHandler({})
  const ChatWidget = ReactWidget.create(<Chat chatHandler={chatHandler}/>);
  ChatWidget.id = 'jupyter-ai::chat';
  ChatWidget.title.icon = psychologyIcon;
  ChatWidget.title.caption = 'Jupyter AI Chat'; // TODO: i18n
  return ChatWidget;
}
