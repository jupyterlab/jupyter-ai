import { INotebookShell } from '@jupyter-notebook/application';
import { IMessageFooterRegistry } from '@jupyter/chat';
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import {
  IWidgetTracker,
  ReactWidget,
  IThemeManager,
  MainAreaWidget,
  ICommandPalette
} from '@jupyterlab/apputils';
import { IDocumentWidget } from '@jupyterlab/docregistry';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { SingletonLayout, Widget } from '@lumino/widgets';

import { chatCommandPlugins } from './chat-command-plugins';
import { completionPlugin } from './completions';
import { StopButton } from './components/message-footer/stop-button';
import { statusItemPlugin } from './status';
import { IJaiCompletionProvider } from './tokens';
import { buildErrorWidget } from './widgets/chat-error';
import { buildAiSettings } from './widgets/settings-widget';

export type DocumentTracker = IWidgetTracker<IDocumentWidget>;

export namespace CommandIDs {
  /**
   * Command to open the AI settings.
   */
  export const openAiSettings = 'jupyter-ai:open-settings';
}

/**
 * Initialization data for the jupyter_ai extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: '@jupyter-ai/core:plugin',
  autoStart: true,
  requires: [IRenderMimeRegistry],
  optional: [
    ICommandPalette,
    IThemeManager,
    IJaiCompletionProvider,
    INotebookShell
  ],
  activate: async (
    app: JupyterFrontEnd,
    rmRegistry: IRenderMimeRegistry,
    palette: ICommandPalette | null,
    themeManager: IThemeManager | null,
    completionProvider: IJaiCompletionProvider | null,
    notebookShell: INotebookShell | null
  ) => {
    const openInlineCompleterSettings = () => {
      app.commands.execute('settingeditor:open', {
        query: 'Inline Completer'
      });
    };

    // Create a AI settings widget.
    let aiSettings: Widget;
    let settingsWidget: ReactWidget;
    try {
      settingsWidget = buildAiSettings(
        themeManager,
        rmRegistry,
        completionProvider,
        openInlineCompleterSettings
      );
    } catch (e) {
      settingsWidget = buildErrorWidget(themeManager);
    }

    // Add a command to open settings widget in main area.
    app.commands.addCommand(CommandIDs.openAiSettings, {
      execute: () => {
        if (!aiSettings || aiSettings.isDisposed) {
          if (notebookShell) {
            aiSettings = new Widget();
            const layout = new SingletonLayout();
            aiSettings.layout = layout;
            layout.widget = settingsWidget;
          } else {
            aiSettings = new MainAreaWidget({ content: settingsWidget });
          }
          aiSettings.id = 'jupyter-ai-settings';
          aiSettings.title.label = 'AI settings';
          aiSettings.title.closable = true;
        }
        if (!aiSettings.isAttached) {
          app?.shell.add(aiSettings, notebookShell ? 'left' : 'main');
        }
        app.shell.activateById(aiSettings.id);
      },
      label: 'AI settings'
    });

    if (palette) {
      palette.addItem({
        category: 'jupyter-ai',
        command: CommandIDs.openAiSettings
      });
    }
  }
};

const stopStreaming: JupyterFrontEndPlugin<void> = {
  id: '@jupyter-ai/core:stop-streaming',
  autoStart: true,
  requires: [IMessageFooterRegistry],
  activate: (app: JupyterFrontEnd, registry: IMessageFooterRegistry) => {
    registry.addSection({
      component: StopButton,
      position: 'center'
    });
  }
};

export default [
  plugin,
  statusItemPlugin,
  completionPlugin,
  stopStreaming,
  ...chatCommandPlugins
];

export * from './contexts';
export * from './tokens';
