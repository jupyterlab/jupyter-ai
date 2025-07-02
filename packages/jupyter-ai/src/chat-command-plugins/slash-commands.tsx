/*
 * Copyright (c) Jupyter Development Team.
 * Distributed under the terms of the Modified BSD License.
 */

import React from 'react';
import { JupyterFrontEndPlugin } from '@jupyterlab/application';
import {
  IChatCommandProvider,
  IChatCommandRegistry,
  IInputModel,
  ChatCommand
} from '@jupyter/chat';
import RefreshIcon from '@mui/icons-material/Refresh';

const SLASH_COMMAND_PROVIDER_ID = '@jupyter-ai/core:slash-command-provider';

/**
 * A command provider that provides completions for slash commands and handles
 * slash command calls.
 *
 * - Slash commands are intended for "chat-level" operations that aren't
 * specific to any persona.
 *
 * - Slash commands may only appear one-at-a-time, and only do something if the
 * first word of the input specifies a slash command `/{slash-command-id}`.
 *
 * - Note: In v2, slash commands were reserved for specific tasks like
 * 'generate' or 'learn'. But because tasks are handled by AI personas via agent
 * tools in v3, slash commands in v3 are reserved for "chat-level" operations
 * that are not specific to an AI persona.
 */
export class SlashCommandProvider implements IChatCommandProvider {
  public id: string = SLASH_COMMAND_PROVIDER_ID;

  /**
   * Regex that matches a potential slash command. The first capturing group
   * captures the ID of the slash command. Slash command IDs may be any
   * combination of: `\`, `-`.
   */
  _regex: RegExp = /\/([\w-]*)/g;

  _slash_commands: ChatCommand[] = [
    {
      name: '/refresh-personas',
      providerId: this.id,
      description: 'Refresh available personas',
      icon: <RefreshIcon />,
      spaceOnAccept: true
    }
  ];

  constructor() {}

  /**
   * Returns slash command completions for the current input.
   */
  async listCommandCompletions(
    inputModel: IInputModel
  ): Promise<ChatCommand[]> {
    // do nothing if not on first word
    const firstWord = getFirstWord(inputModel.value);
    if (inputModel.currentWord !== firstWord) {
      return [];
    }

    // do nothing if first word is not a slash command
    if (!firstWord || !firstWord.startsWith('/')) {
      return [];
    }

    // Return list of commands that complete the first word
    return this._slash_commands.filter(cmd => cmd.name.startsWith(firstWord));
  }

  async onSubmit(inputModel: IInputModel): Promise<void> {
    // no-op. slash commands are handled in the backend
    return;
  }
}

/**
 * Finds the first word in a given string `input`.
 *
 * Returns the first word, or `null` if there is no first word.
 */
function getFirstWord(input: string): string | null {
  let start = 0;

  // Skip leading whitespace
  while (start < input.length && /\s/.test(input[start])) {
    start++;
  }

  // Find end of first word
  let end = start;
  while (end < input.length && !/\s/.test(input[end])) {
    end++;
  }

  const firstWord = input.substring(start, end);
  if (firstWord) {
    return firstWord;
  } else {
    return null;
  }
}

export const slashCommandPlugin: JupyterFrontEndPlugin<void> = {
  id: '@jupyter-ai/core:slash-command-plugin',
  description: 'Adds support for slash commands in Jupyter AI.',
  autoStart: true,
  requires: [IChatCommandRegistry],
  activate: (app, registry: IChatCommandRegistry) => {
    registry.addProvider(new SlashCommandProvider());
  }
};
