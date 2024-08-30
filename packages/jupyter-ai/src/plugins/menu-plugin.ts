import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { IJaiCore } from '../tokens';
import { AiService } from '../handler';
import { Menu } from '@lumino/widgets';
import { CommandRegistry } from '@lumino/commands';

export namespace CommandIDs {
  export const explain = 'jupyter-ai:explain';
  export const fix = 'jupyter-ai:fix';
  export const optimize = 'jupyter-ai:optimize';
  export const refactor = 'jupyter-ai:refactor';
}

/**
 * Optional plugin that adds a "Generative AI" submenu to the context menu.
 * These implement UI shortcuts that explain, fix, refactor, or optimize code in
 * a notebook or file.
 *
 * **This plugin is experimental and may be removed in a future release.**
 */
export const menuPlugin: JupyterFrontEndPlugin<void> = {
  id: '@jupyter-ai/core:menu-plugin',
  autoStart: true,
  requires: [IJaiCore],
  activate: (app: JupyterFrontEnd, jaiCore: IJaiCore) => {
    const { activeCellManager, chatHandler, chatWidget, selectionWatcher } =
      jaiCore;

    function activateChatSidebar() {
      app.shell.activateById(chatWidget.id);
    }

    function getSelection(): AiService.Selection | null {
      const textSelection = selectionWatcher.selection;
      const activeCell = activeCellManager.getContent(false);
      const selection: AiService.Selection | null = textSelection
        ? { type: 'text', source: textSelection.text }
        : activeCell
        ? { type: 'cell', source: activeCell.source }
        : null;

      return selection;
    }

    function buildLabelFactory(baseLabel: string): () => string {
      return () => {
        const textSelection = selectionWatcher.selection;
        const activeCell = activeCellManager.getContent(false);

        return textSelection
          ? `${baseLabel} (${textSelection.numLines} lines selected)`
          : activeCell
          ? `${baseLabel} (1 active cell)`
          : baseLabel;
      };
    }

    // register commands
    const menuCommands = new CommandRegistry();
    menuCommands.addCommand(CommandIDs.explain, {
      execute: () => {
        const selection = getSelection();
        if (!selection) {
          return;
        }

        activateChatSidebar();
        chatHandler.sendMessage({
          prompt: 'Explain the code below.',
          selection
        });
      },
      label: buildLabelFactory('Explain code'),
      isEnabled: () => !!getSelection()
    });
    menuCommands.addCommand(CommandIDs.fix, {
      execute: () => {
        const activeCellWithError = activeCellManager.getContent(true);
        if (!activeCellWithError) {
          return;
        }

        chatHandler.sendMessage({
          prompt: '/fix',
          selection: {
            type: 'cell-with-error',
            error: activeCellWithError.error,
            source: activeCellWithError.source
          }
        });
      },
      label: () => {
        const activeCellWithError = activeCellManager.getContent(true);
        return activeCellWithError
          ? 'Fix code cell (1 error cell)'
          : 'Fix code cell (no error cell)';
      },
      isEnabled: () => {
        const activeCellWithError = activeCellManager.getContent(true);
        return !!activeCellWithError;
      }
    });
    menuCommands.addCommand(CommandIDs.optimize, {
      execute: () => {
        const selection = getSelection();
        if (!selection) {
          return;
        }

        activateChatSidebar();
        chatHandler.sendMessage({
          prompt: 'Optimize the code below.',
          selection
        });
      },
      label: buildLabelFactory('Optimize code'),
      isEnabled: () => !!getSelection()
    });
    menuCommands.addCommand(CommandIDs.refactor, {
      execute: () => {
        const selection = getSelection();
        if (!selection) {
          return;
        }

        activateChatSidebar();
        chatHandler.sendMessage({
          prompt: 'Refactor the code below.',
          selection
        });
      },
      label: buildLabelFactory('Refactor code'),
      isEnabled: () => !!getSelection()
    });

    // add commands as a context menu item containing a "Generative AI" submenu
    const submenu = new Menu({
      commands: menuCommands
    });
    submenu.id = 'jupyter-ai:submenu';
    submenu.title.label = 'Generative AI';
    submenu.addItem({ command: CommandIDs.explain });
    submenu.addItem({ command: CommandIDs.fix });
    submenu.addItem({ command: CommandIDs.optimize });
    submenu.addItem({ command: CommandIDs.refactor });

    app.contextMenu.addItem({
      type: 'submenu',
      selector: '.jp-Editor',
      rank: 1,
      submenu
    });
  }
};
