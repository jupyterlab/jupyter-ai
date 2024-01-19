import { Token } from '@lumino/coreutils';
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
