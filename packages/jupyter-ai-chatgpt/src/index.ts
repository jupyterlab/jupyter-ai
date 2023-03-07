import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

// import type { InsertionContext } from '@jupyter-ai/core';

/**
 * Initialization data for the jupyter-ai-chatgpt extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyter-ai-chatgpt:plugin',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension jupyter-ai-chatgpt is activated!');
  }
};

export default plugin;
