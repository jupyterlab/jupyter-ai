import React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { BigCodeSetting } from '../components/bigcode-settings';
import { bigCodeIcon } from '../icons';

export function buildBigcodeSidebar(): ReactWidget {
  const BigCodeWidget = ReactWidget.create(
    <div>
      <BigCodeSetting />
    </div>
  );

  BigCodeWidget.id = 'jupyter-ai::bigcode-code-Completion';
  BigCodeWidget.title.icon = bigCodeIcon;
  BigCodeWidget.title.caption = 'bigcode code Completion';
  return BigCodeWidget;
}
