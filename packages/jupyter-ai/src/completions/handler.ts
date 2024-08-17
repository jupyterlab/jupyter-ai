import { IDisposable } from '@lumino/disposable';
import { PromiseDelegate } from '@lumino/coreutils';
import { ServerConnection } from '@jupyterlab/services';
import { URLExt } from '@jupyterlab/coreutils';
import { AiCompleterService as AiService } from './types';
import { Signal, ISignal } from '@lumino/signaling';

const SERVICE_URL = 'api/ai/completion/inline';

type StreamChunk = AiService.InlineCompletionStreamChunk;

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

  /**
   * Signal emitted when a new chunk of completion is streamed.
   */
  get streamed(): ISignal<CompletionWebsocketHandler, StreamChunk> {
    return this._streamed;
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
      case 'connection': {
        this._initialized.resolve();
        break;
      }
      case 'stream': {
        this._streamed.emit(message);
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

  private _onClose(e: CloseEvent, reject: (reason: unknown) => void) {
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
    socket.onclose = e => this._onClose(e, promise.reject.bind(promise));
    socket.onerror = e => promise.reject(e);
    socket.onmessage = msg => msg.data && this._onMessage(JSON.parse(msg.data));
  }

  private _isDisposed = false;
  private _socket: WebSocket | null = null;
  private _streamed = new Signal<CompletionWebsocketHandler, StreamChunk>(this);
  private _initialized: PromiseDelegate<void> = new PromiseDelegate<void>();
}
