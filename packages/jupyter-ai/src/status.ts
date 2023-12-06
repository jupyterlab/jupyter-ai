import { IJupyternautStatus } from './tokens';
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { IStatusBar } from '@jupyterlab/statusbar';
import { JupyternautStatus } from './components/statusbar-item';

export const jupyternautStatus: JupyterFrontEndPlugin<IJupyternautStatus> = {
  id: 'jupyter_ai:jupyternaut-status',
  description: 'Adds a status indicator for jupyternaut.',
  autoStart: true,
  optional: [IStatusBar],
  provides: IJupyternautStatus,
  activate: (app: JupyterFrontEnd, statusBar: IStatusBar | null) => {
    const indicator = new JupyternautStatus({ commandRegistry: app.commands });
    if (statusBar) {
      // Add the status item.
      statusBar.registerStatusItem('jupyter_ai:jupyternaut-status', {
        item: indicator,
        align: 'right',
        rank: 100,
        isActive: () => {
          return indicator.hasItems();
        }
      });
    }
    return indicator;
  }
};
