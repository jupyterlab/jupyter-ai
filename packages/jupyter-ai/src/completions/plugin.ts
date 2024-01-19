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
import { displayName, JaiInlineProvider } from './provider';
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

/**
 * Type of the settings object for the inline completer plugin.
 */
type IcPluginSettings = ISettingRegistry.ISettings & {
  user: {
    providers?: {
      [key: string]: unknown;
      [JaiInlineProvider.ID]?: JaiInlineProvider.ISettings;
    };
  };
  composite: {
    providers: {
      [key: string]: unknown;
      [JaiInlineProvider.ID]: JaiInlineProvider.ISettings;
    };
  };
};

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
    const provider = new JaiInlineProvider({
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

    // ic := inline completion
    let icSettings: IcPluginSettings | null = null;

    // jaiIcp := Jupyter AI inline completion provider
    // if not defined, the default settings are used
    let jaiIcpSettings = JaiInlineProvider.DEFAULT_SETTINGS;

    // Reflect changes made by user from Settings Editor
    settingRegistry.pluginChanged.connect(async (_emitter, plugin) => {
      if (plugin !== INLINE_COMPLETER_PLUGIN) {
        return;
      }
      icSettings = (await settingRegistry.load(
        INLINE_COMPLETER_PLUGIN
      )) as IcPluginSettings;
      jaiIcpSettings = icSettings.composite.providers[JaiInlineProvider.ID];
      console.log(jaiIcpSettings);
    });

    /**
     * Updates only the Jupyter AI inline completion provider (JaiIcp) settings.
     * The new settings object is merged with the default JaiIcp settings
     * defined in `JaiInlineProvider.DEFAULT_SETTINGS`.
     *
     * NOTE: This function must not be called before both this plugin,
     * and the core inline completion manager plugin have completed
     * activation. In practice this means that it shall not be awaited
     * from the code activating this plugin.
     *
     * NOTE: This function does not update jaiIcpSettings, which
     * are updated from the composite value in `pluginChanged` callback.
     */
    const updateJaiIcpSettings = async (
      newJaiIcpSettings: Partial<JaiInlineProvider.ISettings>
    ) => {
      if (!icSettings) {
        icSettings = (await settingRegistry.load(
          INLINE_COMPLETER_PLUGIN
        )) as IcPluginSettings;
      }
      const userProvidersSettings = icSettings.user.providers ?? {};
      const newProviders = {
        ...userProvidersSettings,
        [JaiInlineProvider.ID]: {
          ...userProvidersSettings[JaiInlineProvider.ID],
          ...newJaiIcpSettings
        }
      };
      icSettings.set('providers', newProviders);
    };

    app.commands.addCommand(CommandIDs.toggleCompletions, {
      execute: () => {
        updateJaiIcpSettings({ enabled: !jaiIcpSettings.enabled });
      },
      label: 'Enable Jupyternaut Completions',
      isToggled: () => {
        return provider.isEnabled();
      }
    });

    app.commands.addCommand(CommandIDs.toggleLanguageCompletions, {
      execute: () => {
        const language = findCurrentLanguage();
        if (!language) {
          return;
        }

        const disabledLanguages = [...jaiIcpSettings.disabledLanguages];
        const newDisabledLanguages = disabledLanguages.includes(language.name)
          ? disabledLanguages.filter(l => l !== language.name)
          : disabledLanguages.concat(language.name);

        updateJaiIcpSettings({
          disabledLanguages: newDisabledLanguages
        });
      },
      label: () => {
        const language = findCurrentLanguage();
        return language
          ? `Enable Completions in ${displayName(language)}`
          : 'Enable Completions for <language>';
      },
      isToggled: () => {
        const language = findCurrentLanguage();
        return !!language && provider.isLanguageEnabled(language.name);
      },
      isEnabled: () => {
        const language = findCurrentLanguage();
        return !!language && provider.isEnabled();
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
