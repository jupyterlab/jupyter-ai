/*
 * Copyright (c) Jupyter Development Team.
 * Distributed under the terms of the Modified BSD License.
 */

import React from 'react';
import { JupyterFrontEndPlugin } from '@jupyterlab/application';
import type { Contents } from '@jupyterlab/services';
import type { DocumentRegistry } from '@jupyterlab/docregistry';
import {
  IChatCommandProvider,
  IChatCommandRegistry,
  IInputModel,
  ChatCommand
} from '@jupyter/chat';
import FindInPage from '@mui/icons-material/FindInPage';

const FILE_COMMAND_PROVIDER_ID = '@jupyter-ai/core:file-command-provider';

/**
 * A command provider that provides completions for `@file` commands and handles
 * `@file` command calls.
 */
export class FileCommandProvider implements IChatCommandProvider {
  public id: string = FILE_COMMAND_PROVIDER_ID;

  /**
   * Regex that matches all potential `@file` commands. The first capturing
   * group captures the path specified by the user. Paths may contain any
   * combination of:
   *
   * `[a-zA-Z0-9], '/', '-', '_', '.', '@', '\\ ' (escaped space)`
   *
   * IMPORTANT: `+` ensures this regex only matches an occurrence of "@file:" if
   * the captured path is non-empty.
   */
  _regex: RegExp = /@file:(([\w/\-_.@]|\\ )+)/g;

  constructor(
    contentsManager: Contents.IManager,
    docRegistry: DocumentRegistry
  ) {
    this._contentsManager = contentsManager;
    this._docRegistry = docRegistry;
  }

  async listCommandCompletions(
    inputModel: IInputModel
  ): Promise<ChatCommand[]> {
    // do nothing if the current word does not start with '@'.
    const currentWord = inputModel.currentWord;
    if (!currentWord || !currentWord.startsWith('@')) {
      return [];
    }

    // if the current word starts with `@file:`, return a list of valid file
    // paths that complete the currently specified path.
    if (currentWord.startsWith('@file:')) {
      const searchPath = currentWord.split('@file:')[1];
      const commands = await getPathCompletions(
        this._contentsManager,
        this._docRegistry,
        searchPath
      );
      return commands;
    }

    // if the current word matches the start of @file, complete it
    if ('@file'.startsWith(currentWord)) {
      return [
        {
          name: '@file:',
          providerId: this.id,
          description: 'Include a file with your prompt',
          icon: <FindInPage />
        }
      ];
    }

    // otherwise, return nothing as this provider cannot provide any completions
    // for the current word.
    return [];
  }

  async onSubmit(inputModel: IInputModel): Promise<void> {
    // search entire input for valid @file commands using `this._regex`
    const matches = Array.from(inputModel.value.matchAll(this._regex));

    // aggregate all file paths specified by @file commands in the input
    const paths: string[] = [];
    for (const match of matches) {
      if (match.length < 2) {
        continue;
      }
      // `this._regex` contains exactly 1 group that captures the path, so
      // match[1] will contain the path specified by a @file command.
      paths.push(match[1]);
    }

    // add each specified file path as an attachment, unescaping ' ' characters
    // before doing so
    for (let path of paths) {
      path = path.replaceAll('\\ ', ' ');
      inputModel.addAttachment?.({
        type: 'file',
        value: path
      });
    }

    // replace each @file command with the path in an inline Markdown code block
    // for readability, both to humans & to the AI.
    inputModel.value = inputModel.value.replaceAll(
      this._regex,
      (_, path) => `\`${path.replaceAll('\\ ', ' ')}\``
    );

    return;
  }

  private _contentsManager: Contents.IManager;
  private _docRegistry: DocumentRegistry;
}

/**
 * Returns the parent path and base name given a path. The parent path will
 * always include a trailing "/" if non-empty.
 *
 * Examples:
 *  - "package.json" => ["", "package.json"]
 *  - "foo/bar" => ["foo/", "bar"]
 *  - "a/b/c/d.txt" => ["a/b/c/", "d.txt"]
 *
 */
function getParentAndBase(path: string): [string, string] {
  const components = path.split('/');
  let parentPath: string;
  let basename: string;
  if (components.length === 1) {
    parentPath = '';
    basename = components[0];
  } else {
    parentPath = components.slice(0, -1).join('/') + '/';
    basename = components[components.length - 1] ?? '';
  }

  return [parentPath, basename];
}

async function getPathCompletions(
  contentsManager: Contents.IManager,
  docRegistry: DocumentRegistry,
  searchPath: string
): Promise<ChatCommand[]> {
  // get parent directory & the partial basename to be completed
  const [parentPath, basename] = getParentAndBase(searchPath);

  // query the parent directory through the CM, un-escaping spaces beforehand
  const parentDir = await contentsManager.get(
    parentPath.replaceAll('\\ ', ' ')
  );

  const commands: ChatCommand[] = [];

  if (!Array.isArray(parentDir.content)) {
    // return nothing if parentDir is invalid / points to a non-directory file
    return [];
  }

  const children = parentDir.content
    // filter the children of the parent directory to only include file names that
    // start with the specified base name (case-insensitive).
    .filter((a: Contents.IModel) => {
      return a.name.toLowerCase().startsWith(basename.toLowerCase());
    })
    // sort the list, showing directories first while ensuring entries are shown
    // in alphabetic (lexicographically ascending) order.
    .sort((a: Contents.IModel, b: Contents.IModel) => {
      const aPrimaryKey = a.type === 'directory' ? -1 : 1;
      const bPrimaryKey = b.type === 'directory' ? -1 : 1;
      const primaryKey = aPrimaryKey - bPrimaryKey;
      const secondaryKey = a.name < b.name ? -1 : 1;

      return primaryKey || secondaryKey;
    });

  for (const child of children) {
    // get icon
    const { icon } = docRegistry.getFileTypeForModel(child);

    // calculate completion string, escaping any unescaped spaces
    let completion = '@file:' + parentPath + child.name;
    completion = completion.replaceAll(/(?<!\\) /g, '\\ ');

    // add command completion to the list
    let newCommand: ChatCommand;
    const isDirectory = child.type === 'directory';
    if (isDirectory) {
      newCommand = {
        name: child.name + '/',
        providerId: FILE_COMMAND_PROVIDER_ID,
        icon,
        description: 'Search this directory',
        replaceWith: completion + '/'
      };
    } else {
      newCommand = {
        name: child.name,
        providerId: FILE_COMMAND_PROVIDER_ID,
        icon,
        description: 'Attach this file',
        replaceWith: completion,
        spaceOnAccept: true
      };
    }
    commands.push(newCommand);
  }

  return commands;
}

export const fileCommandPlugin: JupyterFrontEndPlugin<void> = {
  id: '@jupyter-ai/core:file-command-plugin',
  description: 'Adds support for the @file command in Jupyter AI.',
  autoStart: true,
  requires: [IChatCommandRegistry],
  activate: (app, registry: IChatCommandRegistry) => {
    const { serviceManager, docRegistry } = app;
    registry.addProvider(
      new FileCommandProvider(serviceManager.contents, docRegistry)
    );
  }
};
