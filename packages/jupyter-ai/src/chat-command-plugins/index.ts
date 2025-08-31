import { fileCommandPlugin } from './file-command';
import { slashCommandPlugin } from './slash-commands';
import { textCommandPlugin } from './text-command';

export const chatCommandPlugins = [
  fileCommandPlugin,
  slashCommandPlugin,
  textCommandPlugin
];
