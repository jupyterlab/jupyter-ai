import { IDisposable } from '@lumino/disposable';
import { ServerConnection } from '@jupyterlab/services';
import { URLExt } from '@jupyterlab/coreutils';
import { Signal } from '@lumino/signaling';

import { AiService } from './handler';

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
  public sendMessage(message: AiService.Request): Promise<string> {
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

  get history(): AiService.ChatHistory {
    return {
      messages: this._messages,
      pending_messages: this._pendingMessages
    };
  }

  get historyChanged(): Signal<this, AiService.ChatHistory> {
    return this._historyChanged;
  }

  private _onMessage(newMessage: AiService.Message): void {
    // resolve promise from `sendMessage()`
    if (newMessage.type === 'human' && newMessage.client.id === this.id) {
      this._sendResolverQueue.shift()?.(newMessage.id);
    }

    // resolve promise from `replyFor()` if it exists
    if (
      newMessage.type === 'agent' &&
      newMessage.reply_to in this._replyForResolverDict
    ) {
      this._replyForResolverDict[newMessage.reply_to](newMessage);
      delete this._replyForResolverDict[newMessage.reply_to];
    }

    // call listeners in serial
    this._listeners.forEach(listener => listener(newMessage));

    // append message to chat history. this block should always set `_messages`
    // or `_pendingMessages` to a new array instance rather than modifying
    // in-place so consumer React components re-render.
    switch (newMessage.type) {
      case 'connection':
        break;
      case 'clear':
        if (newMessage.targets) {
          const targets = newMessage.targets;
          this._messages = this._messages.filter(
            msg =>
              !targets.includes(msg.id) &&
              !('reply_to' in msg && targets.includes(msg.reply_to))
          );
          this._pendingMessages = this._pendingMessages.filter(
            msg => !targets.includes(msg.reply_to)
          );
        } else {
          this._messages = [];
          this._pendingMessages = [];
        }
        break;
      case 'pending':
        this._pendingMessages = [...this._pendingMessages, newMessage];
        break;
      case 'close-pending':
        this._pendingMessages = this._pendingMessages.filter(
          p => p.id !== newMessage.id
        );
        break;
      case 'agent-stream-chunk': {
        const target = newMessage.id;
        const streamMessage = this._messages.find<AiService.AgentStreamMessage>(
          (m): m is AiService.AgentStreamMessage =>
            m.type === 'agent-stream' && m.id === target
        );
        if (!streamMessage) {
          console.error(
            `Received stream chunk with ID ${target}, but no agent-stream message with that ID exists. ` +
              'Ignoring this stream chunk.'
          );
          break;
        }

        streamMessage.body += newMessage.content;
        streamMessage.metadata = newMessage.metadata;
        if (newMessage.stream_complete) {
          streamMessage.complete = true;
        }
        this._messages = [...this._messages];
        break;
      }
      default:
        // human or agent chat message
        this._messages = [...this._messages, newMessage];
        break;
    }

    // finally, trigger `historyChanged` signal
    this._historyChanged.emit({
      messages: this._messages,
      pending_messages: this._pendingMessages
    });
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

        // initialize chat history from `ConnectionMessage`
        this._messages = message.history.messages;
        this._pendingMessages = message.history.pending_messages;

        resolve();
        this.removeListener(listenForConnection);
      };

      this.addListener(listenForConnection);
    });
  }

  private _isDisposed = false;
  private _socket: WebSocket | null = null;
  private _listeners: ((msg: any) => void)[] = [];

  /**
   * The list of chat messages
   */
  private _messages: AiService.ChatMessage[] = [];
  private _pendingMessages: AiService.PendingMessage[] = [];

  /**
   * Signal for when the chat history is changed. Components rendering the chat
   * history should subscribe to this signal and update their state when this
   * signal is triggered.
   */
  private _historyChanged = new Signal<this, AiService.ChatHistory>(this);
}
