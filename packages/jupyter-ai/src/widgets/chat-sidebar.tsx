import React from 'react';
import { ISignal } from '@lumino/signaling';
import { ReactWidget } from '@jupyterlab/apputils';
import type { IThemeManager } from '@jupyterlab/apputils';
import type { Awareness } from 'y-protocols/awareness';

import { Chat } from '../components/chat';
import { chatIcon } from '../icons';
import { SelectionWatcher } from '../selection-watcher';
import { ChatHandler } from '../chat_handler';
import { IJaiCompletionProvider } from '../tokens';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import type { ActiveCellManager } from '../contexts/active-cell-context';

export function buildChatSidebar(
  selectionWatcher: SelectionWatcher,
  chatHandler: ChatHandler,
  globalAwareness: Awareness | null,
  themeManager: IThemeManager | null,
  rmRegistry: IRenderMimeRegistry,
  completionProvider: IJaiCompletionProvider | null,
  openInlineCompleterSettings: () => void,
  activeCellManager: ActiveCellManager,
  focusInputSignal: ISignal<unknown, void>
): ReactWidget {
  const ChatWidget = ReactWidget.create(
    <Chat
      selectionWatcher={selectionWatcher}
      chatHandler={chatHandler}
      globalAwareness={globalAwareness}
      themeManager={themeManager}
      rmRegistry={rmRegistry}
      completionProvider={completionProvider}
      openInlineCompleterSettings={openInlineCompleterSettings}
      activeCellManager={activeCellManager}
      focusInputSignal={focusInputSignal}
    />
  );
  ChatWidget.id = 'jupyter-ai::chat';
  ChatWidget.title.icon = chatIcon;
  ChatWidget.title.caption = 'Jupyter AI Chat'; // TODO: i18n
  return ChatWidget;
}
