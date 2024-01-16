import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ICompletionProviderManager } from '@jupyterlab/completer';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import {
  IEditorLanguageRegistry,
  IEditorLanguage
} from '@jupyterlab/codemirror';
import { getEditor } from '../selection-watcher';
import { IJaiStatusItem } from '../tokens';
import { displayName, JupyterAIInlineProvider } from './provider';
import { CompletionWebsocketHandler } from './handler';

export namespace CommandIDs {
  /**
   * Command to toggle completions globally.
   */
  export const toggleCompletions = 'jupyter-ai:toggle-completions';
  /**
   * Command to toggle completions for specific language.
   */
  export const toggleLanguageCompletions =
    'jupyter-ai:toggle-language-completions';
}

const INLINE_COMPLETER_PLUGIN =
  '@jupyterlab/completer-extension:inline-completer';

export const completionPlugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyter_ai:inline-completions',
  autoStart: true,
  requires: [
    ICompletionProviderManager,
    IEditorLanguageRegistry,
    ISettingRegistry
  ],
  optional: [IJaiStatusItem],
  activate: async (
    app: JupyterFrontEnd,
    completionManager: ICompletionProviderManager,
    languageRegistry: IEditorLanguageRegistry,
    settingRegistry: ISettingRegistry,
    statusItem: IJaiStatusItem | null
  ): Promise<void> => {
    if (typeof completionManager.registerInlineProvider === 'undefined') {
      // Gracefully short-circuit on JupyterLab 4.0 and Notebook 7.0
      console.warn(
        'Inline completions are only supported in JupyterLab 4.1+ and Jupyter Notebook 7.1+'
      );
      return;
    }
    const completionHandler = new CompletionWebsocketHandler();
    const provider = new JupyterAIInlineProvider({
      completionHandler,
      languageRegistry
    });
    await completionHandler.initialize();
    completionManager.registerInlineProvider(provider);

    const findCurrentLanguage = (): IEditorLanguage | null => {
      const widget = app.shell.currentWidget;
      const editor = getEditor(widget);
      if (!editor) {
        return null;
      }
      return languageRegistry.findByMIME(editor.model.mimeType);
    };

    let settings: ISettingRegistry.ISettings | null = null;

    settingRegistry.pluginChanged.connect(async (_emitter, plugin) => {
      if (plugin === INLINE_COMPLETER_PLUGIN) {
        // Only load the settings once the plugin settings were transformed
        settings = await settingRegistry.load(INLINE_COMPLETER_PLUGIN);
      }
    });

    app.commands.addCommand(CommandIDs.toggleCompletions, {
      execute: () => {
        if (!settings) {
          return;
        }
        const providers = Object.assign({}, settings.user.providers) as any;
        const ourSettings = {
          ...JupyterAIInlineProvider.DEFAULT_SETTINGS,
          ...providers[provider.identifier]
        };
        const wasEnabled = ourSettings['enabled'];
        providers[provider.identifier]['enabled'] = !wasEnabled;
        settings.set('providers', providers);
      },
      label: 'Enable Jupyternaut Completions',
      isToggled: () => {
        return provider.isEnabled();
      }
    });

    app.commands.addCommand(CommandIDs.toggleLanguageCompletions, {
      execute: () => {
        const language = findCurrentLanguage();
        if (!settings || !language) {
          return;
        }
        const providers = Object.assign({}, settings.user.providers) as any;
        const ourSettings: JupyterAIInlineProvider.ISettings = {
          ...JupyterAIInlineProvider.DEFAULT_SETTINGS,
          ...providers[provider.identifier]
        };
        const wasDisabled = ourSettings['disabledLanguages'].includes(
          language.name
        );
        const disabledList: string[] =
          providers[provider.identifier]['disabledLanguages'];
        if (wasDisabled) {
          disabledList.filter(name => name !== language.name);
        } else {
          disabledList.push(language.name);
        }
        settings.set('providers', providers);
      },
      label: () => {
        const language = findCurrentLanguage();
        return language
          ? `Enable Completions in ${displayName(language)}`
          : 'Enable Completions for Language of Current Editor';
      },
      isToggled: () => {
        const language = findCurrentLanguage();
        return !!language && provider.isLanguageEnabled(language.name);
      },
      isEnabled: () => {
        return !!findCurrentLanguage() && provider.isEnabled();
      }
    });

    if (statusItem) {
      statusItem.addItem({
        command: CommandIDs.toggleCompletions,
        rank: 1
      });
      statusItem.addItem({
        command: CommandIDs.toggleLanguageCompletions,
        rank: 2
      });
    }
  }
};
