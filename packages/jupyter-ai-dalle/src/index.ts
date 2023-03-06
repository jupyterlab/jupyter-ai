import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { Notebook, NotebookActions } from '@jupyterlab/notebook';
import type { InsertionContext } from '@jupyter-ai/core';

/**
 * Initialization data for the jupyter_ai_dalle extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyter_ai_dalle:plugin',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension jupyter_ai_dalle is activated!');

    // handle below-in-image insertion mode for notebooks
    app.commands.addCommand('ai:insert-below-in-image', {
      execute: ((context: InsertionContext) => {
        const notebook = context.widget;
        if (!(notebook instanceof Notebook)) {
          console.error('Editor widget is not of type "Notebook".');
          return false;
        }

        NotebookActions.insertBelow(notebook);
        NotebookActions.changeCellType(notebook, 'markdown');
        notebook.model?.cells
          .get(notebook.activeCellIndex)
          ?.sharedModel.setSource(`![](${context.response.output})`);
        NotebookActions.run(notebook);
      }) as any
    });
  }
};

export default plugin;
