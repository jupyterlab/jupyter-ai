// This file is based on iconimports.ts in @jupyterlab/ui-components, but is manually generated.

import { LabIcon } from '@jupyterlab/ui-components';

import chatSvgStr from '../style/icons/chat.svg';
import jupyternautSvg from '../style/icons/jupyternaut.svg';
import bigcodeSvg from '../style/icons/bigcode.svg';

export const chatIcon = new LabIcon({
  name: 'jupyter-ai::chat',
  svgstr: chatSvgStr
});

export const jupyternautIcon = new LabIcon({
  name: 'jupyter-ai::jupyternaut',
  svgstr: jupyternautSvg
});

export const bigCodeIcon = new LabIcon({
  name: 'jupyter-ai::code-completion-settings',
  svgstr: bigcodeSvg
});

export const Jupyternaut = jupyternautIcon.react;
