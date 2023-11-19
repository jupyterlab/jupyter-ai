import { Token } from '@lumino/coreutils';
import type { IRankedMenu } from '@jupyterlab/ui-components';

export interface IJupyternautStatus {
  addItem(item: IRankedMenu.IItemOptions): void;
}

/**
 * The Jupyternaut status token.
 */
export const IJupyternautStatus = new Token<IJupyternautStatus>(
  'jupyter_ai:IJupyternautStatus',
  'Status indicator displayed in the statusbar'
);
