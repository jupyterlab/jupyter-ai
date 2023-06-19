import { IDisposable } from '@lumino/disposable';
import { ServerConnection } from '@jupyterlab/services';
import { URLExt } from '@jupyterlab/coreutils';
import { AiService, requestAPI } from './handler';

const CHAT_SERVICE_URL = 'api/ai/chats';

export class ChatHandler implements IDisposable {
  /**
   * The server settings used to make API requests.
   */
  readonly serverSettings: ServerConnection.ISettings;

  /**
   * ID of the connection. Requires `await initialize()`.
   */
  id = '';

  /**
   * Create a new chat handler.
   */
  constructor(options: AiService.IOptions = {}) {
    this.serverSettings =
      options.serverSettings ?? ServerConnection.makeSettings();
  }

  /**
   * Initializes the WebSocket connection to the Chat backend. Promise is
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
  public sendMessage(message: AiService.ChatRequest): Promise<string> {
    return new Promise(resolve => {
      this._socket?.send(JSON.stringify(message));
      this._sendResolverQueue.push(resolve);
    });
  }

  /**
   * Returns a Promise that resolves to the agent's reply, given the message ID
   * of the human message. Should only be called once per message.
   */
  public replyFor(messageId: string): Promise<AiService.AgentChatMessage> {
    return new Promise(resolve => {
      this._replyForResolverDict[messageId] = resolve;
    });
  }

  public addListener(handler: (message: AiService.Message) => void): void {
    this._listeners.push(handler);
  }

  public removeListener(handler: (message: AiService.Message) => void): void {
    const index = this._listeners.indexOf(handler);
    if (index > -1) {
      this._listeners.splice(index, 1);
    }
  }

  public async getHistory(): Promise<AiService.ChatHistory> {
    let data: AiService.ChatHistory = { messages: [] };
    try {
      data = await requestAPI('chats/history', {
        method: 'GET'
      });
    } catch (e) {
      return Promise.reject(e);
    }
    return data;
  }

  /**
   * Whether the chat handler is disposed.
   */
  get isDisposed(): boolean {
    return this._isDisposed;
  }

  /**
   * Dispose the chat handler.
   */
  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    this._isDisposed = true;
    this._listeners = [];

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

  private _onMessage(message: AiService.Message): void {
    // resolve promise from `sendMessage()`
    if (message.type === 'human' && message.client.id === this.id) {
      this._sendResolverQueue.shift()?.(message.id);
    }

    // resolve promise from `replyFor()` if it exists
    if (
      message.type === 'agent' &&
      message.reply_to in this._replyForResolverDict
    ) {
      this._replyForResolverDict[message.reply_to](message);
      delete this._replyForResolverDict[message.reply_to];
    }

    // call listeners in serial
    this._listeners.forEach(listener => listener(message));
  }

  /**
   * Queue of Promise resolvers pushed onto by `send()`
   */
  private _sendResolverQueue: ((value: string) => void)[] = [];

  /**
   * Dictionary mapping message IDs to Promise resolvers, inserted into by
   * `replyFor()`.
   */
  private _replyForResolverDict: Record<
    string,
    (value: AiService.AgentChatMessage) => void
  > = {};

  private _onClose(e: CloseEvent, reject: any) {
    reject(new Error('Chat UI websocket disconnected'));
    console.error('Chat UI websocket disconnected');
    // only attempt re-connect if there was an abnormal closure
    // WebSocket status codes defined in RFC 6455: https://www.rfc-editor.org/rfc/rfc6455.html#section-7.4.1
    if (e.code === 1006) {
      const delaySeconds = 1;
      console.info(`Will try to reconnect in ${delaySeconds} s.`);
      setTimeout(async () => await this._initialize(), delaySeconds * 1000);
    }
  }

  private _initialize(): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      if (this.isDisposed) {
        return;
      }
      console.log('Creating a new websocket connection for chat...');
      const { token, WebSocket, wsUrl } = this.serverSettings;
      const url =
        URLExt.join(wsUrl, CHAT_SERVICE_URL) +
        (token ? `?token=${encodeURIComponent(token)}` : '');

      const socket = (this._socket = new WebSocket(url));
      socket.onclose = e => this._onClose(e, reject);
      socket.onerror = e => reject(e);
      socket.onmessage = msg =>
        msg.data && this._onMessage(JSON.parse(msg.data));

      const listenForConnection = (message: AiService.Message) => {
        if (message.type !== 'connection') {
          return;
        }
        this.id = message.client_id;
        resolve();
        this.removeListener(listenForConnection);
      };

      this.addListener(listenForConnection);
    });
  }

  private _isDisposed = false;
  private _socket: WebSocket | null = null;
  private _listeners: ((msg: any) => void)[] = [];
}
