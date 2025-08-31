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
import TextFieldsIcon from '@mui/icons-material/TextFields';

const TEXT_COMMAND_PROVIDER_ID = '@jupyter-ai/core:text-command-provider';

/**
 * A command provider that provides completions for `@text` commands and handles
 * `@text` command calls.
 */
export class TextCommandProvider implements IChatCommandProvider {
  public id: string = TEXT_COMMAND_PROVIDER_ID;

  /**
   * Regex that matches all potential `@text` commands. The first capturing
   * group captures the text type specified by the user.
   */
  _regex: RegExp = /@text:(active_cell|selected_text)/g;

  async listCommandCompletions(
    inputModel: IInputModel
  ): Promise<ChatCommand[]> {
    // do nothing if the current word does not start with '@'.
    const currentWord = inputModel.currentWord;
    if (!currentWord || !currentWord.startsWith('@')) {
      return [];
    }

    // Check if any text options are available
    const hasActiveCell = inputModel.activeCellManager?.available;
    const hasSelectedText = !!inputModel.selectionWatcher?.selection;

    // Don't show @text at all if no options are available
    if (!hasActiveCell && !hasSelectedText) {
      return [];
    }

    // if the current word starts with `@text:`, return filtered text type completions
    if (currentWord.startsWith('@text:')) {
      const searchText = currentWord.split('@text:')[1];
      const commands: ChatCommand[] = [];

      // Add active_cell option if available and matches search
      if (hasActiveCell && 'active_cell'.startsWith(searchText)) {
        commands.push({
          name: '@text:active_cell',
          providerId: this.id,
          icon: <TextFieldsIcon />,
          description: 'Include active cell content',
          replaceWith: '@text:active_cell',
          spaceOnAccept: true
        });
      }

      // Add selected_text option if available and matches search
      if (hasSelectedText && 'selected_text'.startsWith(searchText)) {
        commands.push({
          name: '@text:selected_text',
          providerId: this.id,
          icon: <TextFieldsIcon />,
          description: 'Include selected text',
          replaceWith: '@text:selected_text',
          spaceOnAccept: true
        });
      }

      return commands;
    }

    // if the current word matches the start of @text, complete it
    if ('@text'.startsWith(currentWord)) {
      return [
        {
          name: '@text:',
          providerId: this.id,
          description: 'Include text content',
          icon: <TextFieldsIcon />
        }
      ];
    }

    // otherwise, return nothing as this provider cannot provide any completions
    // for the current word.
    return [];
  }

  async onSubmit(inputModel: IInputModel): Promise<void> {
    // replace each @text command with the actual content as markdown code blocks
    inputModel.value = inputModel.value.replaceAll(
      this._regex,
      (match, textType) => {
        let source = '';
        let language: string | undefined;

        if (
          textType === 'active_cell' &&
          inputModel.activeCellManager?.available
        ) {
          const cellContent = inputModel.activeCellManager.getContent(false);
          if (cellContent) {
            source = cellContent.source;
            language = cellContent.language;
          }
        } else if (
          textType === 'selected_text' &&
          inputModel.selectionWatcher?.selection
        ) {
          const selection = inputModel.selectionWatcher.selection;
          source = selection.text;
          language = selection.language;
        }

        if (source) {
          return `

\`\`\`${language ?? ''}
${source}
\`\`\`
`;
        }

        // fallback if no content found
        return `\`${textType}\``;
      }
    );

    return;
  }
}

export const textCommandPlugin: JupyterFrontEndPlugin<void> = {
  id: '@jupyter-ai/core:text-command-plugin',
  description: 'Adds support for the @text command in Jupyter AI.',
  autoStart: true,
  requires: [IChatCommandRegistry],
  activate: (app, registry: IChatCommandRegistry) => {
    registry.addProvider(new TextCommandProvider());
  }
};