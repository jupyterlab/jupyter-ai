import { IDisposable } from '@lumino/disposable';
import { ServerConnection } from '@jupyterlab/services';
import { Signal } from '@lumino/signaling';
import { URLExt } from '@jupyterlab/coreutils';
import {Poll} from '@lumino/polling';


/**
 * The url for the chat api
 */
const CHAT_SERVICE_URL = 'api/ai/chats';

export class ChatHandler implements IDisposable{
  /**
   * Create a new event manager.
   */
  constructor(options: ChatHandler.IOptions = {}) {
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
   * Whether the event manager is disposed.
   */
  get isDisposed(): boolean {
    return this._isDisposed;
  }

   /**
   * Dispose the event manager.
   */
   dispose(): void {
    if (this.isDisposed) {
      return;
    }
    this._isDisposed = true;

    // Clean up poll.
    this._poll.dispose();

    this._listeners = []

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

    // Clean up stream.
    Signal.clearData(this);
  }

  public addListener(handler: (msg: any) => void): void {
    this._listeners.push(handler);
  }

  public sendMessage(msg: any): void {
    this._socket?.send(msg)
  }

  private _onMessage(msg: any): void {
    this._listeners.forEach(listener => listener(msg));
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

        socket.onclose = () => reject(new Error('EventManager socket closed'));
        socket.onmessage = msg => msg.data && this._onMessage(JSON.parse(msg.data));
    });

  }

  private _isDisposed = false;
  private _poll: Poll;
  private _socket: WebSocket | null = null;
  private _listeners:  ((msg: any) => void)[] = [];
}

/**
 * A namespace for `EventManager` statics.
 */
export namespace ChatHandler {
    /**
     * The instantiation options for an event manager.
     */
    export interface IOptions {
      /**
       * The server settings used to make API requests.
       */
      serverSettings?: ServerConnection.ISettings;
    }
}