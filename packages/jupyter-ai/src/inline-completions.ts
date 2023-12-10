import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import {
  ICompletionProviderManager,
  IInlineCompletionProvider,
  IInlineCompletionContext,
  CompletionHandler
} from '@jupyterlab/completer';
import type { ISettingRegistry } from '@jupyterlab/settingregistry';

import { IDisposable } from '@lumino/disposable';
import { JSONValue, PromiseDelegate } from '@lumino/coreutils';
import { ServerConnection } from '@jupyterlab/services';
import { URLExt } from '@jupyterlab/coreutils';
import { IEditorLanguageRegistry } from '@jupyterlab/codemirror';
import { NotebookPanel } from '@jupyterlab/notebook';
import { AiService } from './handler';
import { DocumentWidget } from '@jupyterlab/docregistry';
import { Signal, ISignal } from '@lumino/signaling';

const SERVICE_URL = 'api/ai/completion/inline';

export class CompletionWebsocketHandler implements IDisposable {
  /**
   * The server settings used to make API requests.
   */
  readonly serverSettings: ServerConnection.ISettings;

  /**
   * Create a new completion handler.
   */
  constructor(options: AiService.IOptions = {}) {
    this.serverSettings =
      options.serverSettings ?? ServerConnection.makeSettings();
  }

  /**
   * Initializes the WebSocket connection to the completion backend. Promise is
   * resolved when server acknowledges connection and sends the client ID. This
   * must be awaited before calling any other method.
   */
  public async initialize(): Promise<void> {
    await this._initialize();
  }

  /**
   * Sends a message across the WebSocket. Promise resolves to the message ID
   * when the server sends the same message back, acknowledging receipt.
   */
  public sendMessage(
    message: AiService.InlineCompletionRequest
  ): Promise<AiService.InlineCompletionReply> {
    return new Promise(resolve => {
      this._socket?.send(JSON.stringify(message));
      this._replyForResolver[message.number] = resolve;
    });
  }

  get modelChanged(): ISignal<CompletionWebsocketHandler, string> {
    return this._modelChanged;
  }

  /**
   * Whether the completion handler is disposed.
   */
  get isDisposed(): boolean {
    return this._isDisposed;
  }

  /**
   * Dispose the completion handler.
   */
  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    this._isDisposed = true;

    // Clean up socket.
    const socket = this._socket;
    if (socket) {
      this._socket = null;
      socket.onopen = () => undefined;
      socket.onerror = () => undefined;
      socket.onmessage = () => undefined;
      socket.onclose = () => undefined;
      socket.close();
    }
  }

  private _onMessage(message: AiService.CompleterMessage): void {
    switch (message.type) {
      case 'model_changed': {
        this._modelChanged.emit(message.model);
        break;
      }
      case 'connection': {
        this._initialized.resolve();
        break;
      }
      default: {
        if (message.reply_to in this._replyForResolver) {
          this._replyForResolver[message.reply_to](message);
          delete this._replyForResolver[message.reply_to];
        } else {
          console.warn('Unhandled message', message);
        }
        break;
      }
    }
  }

  /**
   * Dictionary mapping message IDs to Promise resolvers.
   */
  private _replyForResolver: Record<
    number,
    (value: AiService.InlineCompletionReply) => void
  > = {};

  private _onClose(e: CloseEvent, reject: any) {
    reject(new Error('Inline completion websocket disconnected'));
    console.error('Inline completion websocket disconnected');
    // only attempt re-connect if there was an abnormal closure
    // WebSocket status codes defined in RFC 6455: https://www.rfc-editor.org/rfc/rfc6455.html#section-7.4.1
    if (e.code === 1006) {
      const delaySeconds = 1;
      console.info(`Will try to reconnect in ${delaySeconds} s.`);
      setTimeout(async () => await this._initialize(), delaySeconds * 1000);
    }
  }

  private async _initialize(): Promise<void> {
    if (this.isDisposed) {
      return;
    }
    const promise = new PromiseDelegate<void>();
    this._initialized = promise;
    console.log(
      'Creating a new websocket connection for inline completions...'
    );
    const { token, WebSocket, wsUrl } = this.serverSettings;
    const url =
      URLExt.join(wsUrl, SERVICE_URL) +
      (token ? `?token=${encodeURIComponent(token)}` : '');

    const socket = (this._socket = new WebSocket(url));
    socket.onclose = e => this._onClose(e, promise.reject);
    socket.onerror = e => promise.reject(e);
    socket.onmessage = msg => msg.data && this._onMessage(JSON.parse(msg.data));
  }

  private _isDisposed = false;
  private _socket: WebSocket | null = null;
  private _modelChanged = new Signal<CompletionWebsocketHandler, string>(this);
  private _initialized: PromiseDelegate<void> = new PromiseDelegate<void>();
}

class JupyterAIInlineProvider implements IInlineCompletionProvider {
  readonly identifier = 'jupyter-ai';

  constructor(protected options: JupyterAIInlineProvider.IOptions) {
    options.completionHandler.modelChanged.connect(
      (_emitter, model: string) => {
        this._currentModel = model;
      }
    );
  }

  get name() {
    return `JupyterAI (${this._currentModel})`;
  }

  async fetch(
    request: CompletionHandler.IRequest,
    context: IInlineCompletionContext
  ) {
    console.log(context.widget instanceof NotebookPanel, context.widget);
    let cellId = undefined;
    let path = context.session?.path;
    if (context.widget instanceof NotebookPanel) {
      const activeCell = context.widget.content.activeCell;
      if (activeCell) {
        cellId = activeCell.model.id;
      }
    }
    if (!path && context.widget instanceof DocumentWidget) {
      path = context.widget.context.path;
    }
    const number = ++this._counter;
    const mime = request.mimeType ?? 'text/plain';
    const language = this.options.languageRegistry.findByMIME(mime);
    const result = await this.options.completionHandler.sendMessage({
      path: context.session?.path,
      mime,
      prefix: this._prefixFromRequest(request),
      suffix: this._suffixFromRequest(request),
      language: language ? language.name : 'plain English',
      number,
      cell_id: cellId
    });
    return result.list;
  }

  get schema(): ISettingRegistry.IProperty {
    return {
      properties: {
        maxPrefix: {
          title: 'Maximum prefix length',
          minimum: 1,
          type: 'number',
          description:
            'At most how many prefix characters should be provided to the model.'
        },
        maxSuffix: {
          title: 'Maximum suffix length',
          minimum: 0,
          type: 'number',
          description:
            'At most how many suffix characters should be provided to the model.'
        }
      },
      default: JupyterAIInlineProvider.DEFAULT_SETTINGS as any
    };
  }

  async configure(settings: { [property: string]: JSONValue }): Promise<void> {
    this._settings = settings as any as JupyterAIInlineProvider.ISettings;
  }

  /**
   * Extract prefix from request, accounting for context window limit.
   */
  private _prefixFromRequest(request: CompletionHandler.IRequest): string {
    const textBefore = request.text.slice(0, request.offset);
    const prefix = textBefore.slice(
      -Math.min(this._settings.maxPrefix, textBefore.length)
    );
    return prefix;
  }

  /**
   * Extract suffix from request, accounting for context window limit.
   */
  private _suffixFromRequest(request: CompletionHandler.IRequest): string {
    const textAfter = request.text.slice(request.offset);
    const prefix = textAfter.slice(
      0,
      Math.min(this._settings.maxPrefix, textAfter.length)
    );
    return prefix;
  }

  private _settings: JupyterAIInlineProvider.ISettings =
    JupyterAIInlineProvider.DEFAULT_SETTINGS;

  private _currentModel = 'no-model-yet';
  private _counter = 0;
}

namespace JupyterAIInlineProvider {
  export interface IOptions {
    completionHandler: CompletionWebsocketHandler;
    languageRegistry: IEditorLanguageRegistry;
  }
  export interface ISettings {
    maxPrefix: number;
    maxSuffix: number;
  }
  export const DEFAULT_SETTINGS: ISettings = {
    maxPrefix: 10000,
    maxSuffix: 10000
  };
}

export const inlineCompletionProvider: JupyterFrontEndPlugin<void> = {
  id: 'jupyter_ai:inline-completions',
  autoStart: true,
  requires: [ICompletionProviderManager, IEditorLanguageRegistry],
  activate: async (
    app: JupyterFrontEnd,
    manager: ICompletionProviderManager,
    languageRegistry: IEditorLanguageRegistry
  ): Promise<void> => {
    const completionHandler = new CompletionWebsocketHandler();
    const provider = new JupyterAIInlineProvider({
      completionHandler,
      languageRegistry
    });
    await completionHandler.initialize();
    manager.registerInlineProvider(provider);
  }
};
