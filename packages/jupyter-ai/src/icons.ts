// This file is based on iconimports.ts in @jupyterlab/ui-components, but is manually generated.

import { LabIcon } from '@jupyterlab/ui-components';

import chatSvgStr from '../style/icons/chat.svg';
import jupyternautSvg from '../style/icons/jupyternaut.svg';

export const chatIcon = new LabIcon({
  name: 'jupyter-ai::chat',
  svgstr: chatSvgStr
});

export const jupyternautIcon = new LabIcon({
  name: 'jupyter-ai::jupyternaut',
  svgstr: jupyternautSvg
});

// this icon is only used in the status bar.
// to configure the icon shown on agent replies in the chat UI, please specify a
// custom `Persona`.
export const Jupyternaut = jupyternautIcon.react;
