import { fileCommandPlugin } from './file-command';
import { slashCommandPlugin } from './slash-commands';
import { selectionCommandPlugin } from './text-command';

export const chatCommandPlugins = [
  fileCommandPlugin,
  slashCommandPlugin,
  selectionCommandPlugin
];
