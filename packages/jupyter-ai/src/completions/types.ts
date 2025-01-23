import type {
  IInlineCompletionList,
  IInlineCompletionItem
} from '@jupyterlab/completer';

import { ServerConnection } from '@jupyterlab/services';

export namespace AiCompleterService {
  /**
   * The instantiation options for a data registry handler.
   */
  export interface IOptions {
    serverSettings?: ServerConnection.ISettings;
  }

  export type ConnectionMessage = {
    type: 'connection';
    client_id: string;
  };

  export type InlineCompletionRequest = {
    number: number;
    path?: string;
    /* The model has to complete given prefix */
    prefix: string;
    /* The model may consider the following suffix */
    suffix: string;
    mime: string;
    /* Whether to stream the response (if streaming is supported by the model) */
    stream: boolean;
    language?: string;
    cell_id?: string;
  };

  export type CompletionError = {
    type: string;
    traceback: string;
    title: string;
  };

  export type InlineCompletionReply = {
    /**
     * Type for this message can be skipped (`inline_completion` is presumed default).
     **/
    type?: 'inline_completion';
    list: IInlineCompletionList;
    reply_to: number;
    error?: CompletionError;
  };

  export type InlineCompletionStreamChunk = {
    type: 'stream';
    response: IInlineCompletionItem;
    reply_to: number;
    done: boolean;
  };

  export type CompleterMessage =
    | InlineCompletionReply
    | ConnectionMessage
    | InlineCompletionStreamChunk;
}
