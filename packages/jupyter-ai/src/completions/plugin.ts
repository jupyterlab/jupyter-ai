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
import { IJaiStatusItem, IJaiCompletionProvider } from '../tokens';
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

type JaiCompletionToken = IJaiCompletionProvider | null;

export const completionPlugin: JupyterFrontEndPlugin<JaiCompletionToken> = {
  id: '@jupyter-ai/core:inline-completions',
  autoStart: true,
  requires: [
    ICompletionProviderManager,
    IEditorLanguageRegistry,
    ISettingRegistry
  ],
  optional: [IJaiStatusItem],
  provides: IJaiCompletionProvider,
  activate: async (
    app: JupyterFrontEnd,
    completionManager: ICompletionProviderManager,
    languageRegistry: IEditorLanguageRegistry,
    settingRegistry: ISettingRegistry,
    statusItem: IJaiStatusItem | null
  ): Promise<JaiCompletionToken> => {
    if (typeof completionManager.registerInlineProvider === 'undefined') {
      // Gracefully short-circuit on JupyterLab 4.0 and Notebook 7.0
      console.warn(
        'Inline completions are only supported in JupyterLab 4.1+ and Jupyter Notebook 7.1+'
      );
      return null;
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
    async function getIcSettings() {
      return (await settingRegistry.load(
        INLINE_COMPLETER_PLUGIN
      )) as IcPluginSettings;
    }

    /**
     * Gets the composite settings for the Jupyter AI inline completion provider
     * (JaiIcp).
     *
     * This reads from the `ISettings.composite` property, which merges the user
     * settings with the provider defaults, defined in
     * `JaiInlineProvider.DEFAULT_SETTINGS`.
     */
    async function getJaiIcpSettings() {
      const icSettings = await getIcSettings();
      return icSettings.composite.providers[JaiInlineProvider.ID];
    }

    /**
     * Updates the JaiIcp user settings.
     */
    async function updateJaiIcpSettings(
      newJaiIcpSettings: Partial<JaiInlineProvider.ISettings>
    ) {
      const icSettings = await getIcSettings();
      const oldUserIcpSettings = icSettings.user.providers;
      const newUserIcpSettings = {
        ...oldUserIcpSettings,
        [JaiInlineProvider.ID]: {
          ...oldUserIcpSettings?.[JaiInlineProvider.ID],
          ...newJaiIcpSettings
        }
      };
      icSettings.set('providers', newUserIcpSettings);
    }

    app.commands.addCommand(CommandIDs.toggleCompletions, {
      execute: async () => {
        const jaiIcpSettings = await getJaiIcpSettings();
        updateJaiIcpSettings({
          enabled: !jaiIcpSettings.enabled
        });
      },
      label: 'Enable completions by Jupyternaut',
      isToggled: () => {
        return provider.isEnabled();
      }
    });

    app.commands.addCommand(CommandIDs.toggleLanguageCompletions, {
      execute: async () => {
        const jaiIcpSettings = await getJaiIcpSettings();
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
          ? `Disable completions in ${displayName(language)}`
          : 'Disable completions in <language> files';
      },
      isToggled: () => {
        const language = findCurrentLanguage();
        return !!language && !provider.isLanguageEnabled(language.name);
      },
      isVisible: () => {
        const language = findCurrentLanguage();
        return !!language;
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
    return provider;
  }
};
