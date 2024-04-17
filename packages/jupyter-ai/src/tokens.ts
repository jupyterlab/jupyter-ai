import { Token } from '@lumino/coreutils';
import { ISignal } from '@lumino/signaling';
import type { IRankedMenu } from '@jupyterlab/ui-components';

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
 * The incline completion provider token.
 */
export const IJaiCompletionProvider = new Token<IJaiCompletionProvider>(
  'jupyter_ai:IJaiCompletionProvider',
  'Status the incline completion provider'
);
