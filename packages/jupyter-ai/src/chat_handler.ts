import { IDisposable } from '@lumino/disposable';
import { ServerConnection } from '@jupyterlab/services';
import { Signal } from '@lumino/signaling';
import { URLExt } from '@jupyterlab/coreutils';
import {Poll} from '@lumino/polling';


const API_NAMESPACE = 'api/ai';

/**
 * Call the API extension
 *
 * @param endPoint API REST end point for the extension
 * @param init Initial values for the request
 * @returns The response body interpreted as JSON
 */
export async function requestAPI<T>(
  endPoint = '',
  init: RequestInit = {}
): Promise<T> {
  // Make request to Jupyter API
  const settings = ServerConnection.makeSettings();
  const requestUrl = URLExt.join(settings.baseUrl, API_NAMESPACE, endPoint);

  let response: Response;
  try {
    response = await ServerConnection.makeRequest(requestUrl, init, settings);
  } catch (error) {
    throw new ServerConnection.NetworkError(error as TypeError);
  }

  let data: any = await response.text();

  if (data.length > 0) {
    try {
      data = JSON.parse(data);
    } catch (error) {
      console.log('Not a JSON response body.', response);
    }
  }

  if (!response.ok) {
    throw new ServerConnection.ResponseError(response, data.message || data);
  }

  return data;
}

const CHAT_SERVICE_URL = "api/ai/chats"

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

  public removeListener(handler: (msg: any) => void): void {
    const index = this._listeners.indexOf(handler)
    if(index > -1) {
      this._listeners.splice(index, 1)
    }
  }

  public sendMessage(msg: any): void {
    this._socket?.send(msg)
  }

  public async getHistory(): Promise<any[]> {
    console.log("Going to get the history messages...")
    let data: any[] = []
    try {
      data = await requestAPI('chats/history', {
        method: 'GET'
      });
    } catch (e) {
      return Promise.reject(e);
    }
    return data;
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