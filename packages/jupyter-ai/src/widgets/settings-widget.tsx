import React from 'react';
import { IThemeManager, ReactWidget } from '@jupyterlab/apputils';
import { settingsIcon } from '@jupyterlab/ui-components';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import { IJaiCompletionProvider } from '../tokens';
import { ChatSettings } from '../components/chat-settings';
import { JlThemeProvider } from '../components/jl-theme-provider';

export function buildAiSettings(
  themeManager: IThemeManager | null,
  rmRegistry: IRenderMimeRegistry,
  completionProvider: IJaiCompletionProvider | null,
  openInlineCompleterSettings: () => void
): ReactWidget {
  const SettingsWidget = ReactWidget.create(
    <JlThemeProvider themeManager={themeManager}>
      <ChatSettings
        rmRegistry={rmRegistry}
        completionProvider={completionProvider}
        openInlineCompleterSettings={openInlineCompleterSettings}
        inputOptions={false}
      />
    </JlThemeProvider>
  );
  SettingsWidget.id = 'jupyter-ai::settings';
  SettingsWidget.title.icon = settingsIcon;
  SettingsWidget.title.caption = 'Jupyter AI Settings'; // TODO: i18n
  return SettingsWidget;
}
