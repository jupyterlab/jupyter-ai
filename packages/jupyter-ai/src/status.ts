import { IJaiStatusItem } from './tokens';
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { IStatusBar } from '@jupyterlab/statusbar';
import { JaiStatusItem } from './components/statusbar-item';

export const statusItemPlugin: JupyterFrontEndPlugin<IJaiStatusItem> = {
  id: 'jupyter_ai:status-item',
  description: 'Provides a status item for Jupyter AI.',
  autoStart: true,
  optional: [IStatusBar],
  provides: IJaiStatusItem,
  activate: (app: JupyterFrontEnd, statusBar: IStatusBar | null) => {
    const statusItem = new JaiStatusItem({
      commandRegistry: app.commands
    });
    if (statusBar) {
      // Add the status item.
      statusBar.registerStatusItem('jupyter_ai:jupyternaut-status', {
        item: statusItem,
        align: 'right',
        rank: 100,
        isActive: () => {
          return statusItem.hasItems();
        }
      });
    }
    return statusItem;
  }
};
