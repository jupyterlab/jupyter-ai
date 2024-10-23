import React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { settingsIcon } from '@jupyterlab/ui-components';

import { IJaiCompletionProvider } from '../tokens';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { ChatSettings } from '../components/chat-settings';

export function buildAiSettings(
  rmRegistry: IRenderMimeRegistry,
  completionProvider: IJaiCompletionProvider | null,
  openInlineCompleterSettings: () => void
): ReactWidget {
  const SettingsWidget = ReactWidget.create(
    <ChatSettings
      rmRegistry={rmRegistry}
      completionProvider={completionProvider}
      openInlineCompleterSettings={openInlineCompleterSettings}
      inputOptions={false}
    />
  );
  SettingsWidget.id = 'jupyter-ai::settings';
  SettingsWidget.title.icon = settingsIcon;
  SettingsWidget.title.caption = 'Jupyter AI Settings'; // TODO: i18n
  return SettingsWidget;
}
