import React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { BigCodeSetting } from "../components/bigcode-settings"
import { chatIcon } from '../icons';

export function buildBigcodeSidebar(): ReactWidget {
  const BigCodeWidget = ReactWidget.create(
    <div>
      <BigCodeSetting/>
    </div>
  );
  
  BigCodeWidget.id = 'jupyter-ai::bigcode';
  BigCodeWidget.title.icon = chatIcon;
  BigCodeWidget.title.caption = 'bigcode continuation';
  return BigCodeWidget;
}