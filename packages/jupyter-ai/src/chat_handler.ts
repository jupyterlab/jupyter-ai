import { IDisposable } from '@lumino/disposable';
import { ServerConnection } from '@jupyterlab/services';
import { URLExt } from '@jupyterlab/coreutils';
import { Poll } from '@lumino/polling';
import { AiService, requestAPI } from './handler';

const CHAT_SERVICE_URL = 'api/ai/chats';

export class ChatHandler implements IDisposable {
  /**
   * Create a new chat handler.
   */
  constructor(options: AiService.IOptions = {}) {
    this.serverSettings =
      options.serverSettings ?? ServerConnection.makeSettings();

    this._poll = new Poll({ factory: () => this._subscribe() });
    this._poll.start();
  }

  /**
   * The server settings used to make API requests.
   */
  readonly serverSettings: ServerConnection.ISettings;

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

    // Clean up poll.
    this._poll.dispose();

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

  public addListener(handler: (message: AiService.ChatMessage) => void): void {
    this._listeners.push(handler);
  }

  public removeListener(
    handler: (message: AiService.ChatMessage) => void
  ): void {
    const index = this._listeners.indexOf(handler);
    if (index > -1) {
      this._listeners.splice(index, 1);
    }
  }

  public sendMessage(message: AiService.ChatRequest): void {
    this._socket?.send(JSON.stringify(message));
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

  private _onMessage(message: AiService.ChatMessage): void {
    this._listeners.forEach(listener => listener(message));
  }

  private _subscribe(): Promise<void> {
    return new Promise<void>((_, reject) => {
      if (this.isDisposed) {
        return;
      }
      const { token, WebSocket, wsUrl } = this.serverSettings;
      const url =
        URLExt.join(wsUrl, CHAT_SERVICE_URL) +
        (token ? `?token=${encodeURIComponent(token)}` : '');
      const socket = (this._socket = new WebSocket(url));

      socket.onclose = () => reject(new Error('ChatHandler socket closed'));
      socket.onmessage = msg =>
        msg.data && this._onMessage(JSON.parse(msg.data));
    });
  }

  private _isDisposed = false;
  private _poll: Poll;
  private _socket: WebSocket | null = null;
  private _listeners: ((msg: any) => void)[] = [];
}
