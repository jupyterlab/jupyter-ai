import React from 'react';
import { Token } from '@lumino/coreutils';
import { ISignal } from '@lumino/signaling';
import type { IRankedMenu, ReactWidget } from '@jupyterlab/ui-components';

import { AiService } from './handler';
import { ChatHandler } from './chat_handler';
import { ActiveCellManager } from './contexts/active-cell-context';
import { SelectionWatcher } from './selection-watcher';

export interface IJaiStatusItem {
  addItem(item: IRankedMenu.IItemOptions): void;
}

/**
 * The Jupyternaut status token.
 */
export const IJaiStatusItem = new Token<IJaiStatusItem>(
  'jupyter_ai:IJupyternautStatus',
  'Status indicator displayed in the statusbar'
);

export interface IJaiCompletionProvider {
  isEnabled(): boolean;
  settingsChanged: ISignal<IJaiCompletionProvider, void>;
}

/**
 * The inline completion provider token.
 */
export const IJaiCompletionProvider = new Token<IJaiCompletionProvider>(
  'jupyter_ai:IJaiCompletionProvider',
  'The jupyter-ai inline completion provider API'
);

export type IJaiMessageFooterProps = {
  message: AiService.ChatMessage;
};

export interface IJaiMessageFooter {
  component: React.FC<IJaiMessageFooterProps>;
}

/**
 * The message footer provider token. Another extension should provide this
 * token to add a footer to each message.
 */

export const IJaiMessageFooter = new Token<IJaiMessageFooter>(
  'jupyter_ai:IJaiMessageFooter',
  'Optional component that is used to render a footer on each Jupyter AI chat message, when provided.'
);

export interface IJaiCore {
  chatWidget: ReactWidget;
  chatHandler: ChatHandler;
  activeCellManager: ActiveCellManager;
  selectionWatcher: SelectionWatcher;
}

/**
 * The Jupyter AI core provider token. Frontend plugins that want to extend the
 * Jupyter AI frontend by adding features which send messages or observe the
 * current text selection & active cell should require this plugin.
 */
export const IJaiCore = new Token<IJaiCore>(
  'jupyter_ai:core',
  'The core implementation of the frontend.'
);
