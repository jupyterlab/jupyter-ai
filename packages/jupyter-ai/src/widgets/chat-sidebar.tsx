import React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import type { IThemeManager } from '@jupyterlab/apputils';
import type { Awareness } from 'y-protocols/awareness';

import { Chat } from '../components/chat';
import { chatIcon } from '../icons';
import { SelectionWatcher } from '../selection-watcher';
import { ChatHandler } from '../chat_handler';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

export function buildChatSidebar(
  selectionWatcher: SelectionWatcher,
  chatHandler: ChatHandler,
  globalAwareness: Awareness | null,
  themeManager: IThemeManager | null,
  rmRegistry: IRenderMimeRegistry
): ReactWidget {
  const ChatWidget = ReactWidget.create(
    <Chat
      selectionWatcher={selectionWatcher}
      chatHandler={chatHandler}
      globalAwareness={globalAwareness}
      themeManager={themeManager}
      rmRegistry={rmRegistry}
    />
  );
  ChatWidget.id = 'jupyter-ai::chat';
  ChatWidget.title.icon = chatIcon;
  ChatWidget.title.caption = 'Jupyter AI Chat'; // TODO: i18n
  return ChatWidget;
}
