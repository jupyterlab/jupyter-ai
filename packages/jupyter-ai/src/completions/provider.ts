import {
  InlineCompletionTriggerKind,
  IInlineCompletionProvider,
  IInlineCompletionContext,
  IInlineCompletionList,
  IInlineCompletionItem,
  CompletionHandler
} from '@jupyterlab/completer';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { Notification, showErrorMessage } from '@jupyterlab/apputils';
import { JSONValue, PromiseDelegate } from '@lumino/coreutils';
import { ISignal, Signal } from '@lumino/signaling';
import {
  IEditorLanguageRegistry,
  IEditorLanguage
} from '@jupyterlab/codemirror';
import { NotebookPanel } from '@jupyterlab/notebook';
import { IJaiCompletionProvider } from '../tokens';
import { AiCompleterService as AiService } from './types';
import { DocumentWidget } from '@jupyterlab/docregistry';
import { jupyternautIcon } from '../icons';
import { CompletionWebsocketHandler } from './handler';

type StreamChunk = AiService.InlineCompletionStreamChunk;

/**
 * Format the language name nicely.
 */
export function displayName(language: IEditorLanguage): string {
  if (language.name === 'ipythongfm') {
    return 'Markdown (IPython)';
  }
  if (language.name === 'ipython') {
    return 'IPython';
  }
  return language.displayName ?? language.name;
}

export class JaiInlineProvider
  implements IInlineCompletionProvider, IJaiCompletionProvider
{
  readonly identifier = JaiInlineProvider.ID;
  readonly icon = jupyternautIcon.bindprops({ width: 16, top: 1 });

  constructor(protected options: JaiInlineProvider.IOptions) {
    options.completionHandler.streamed.connect(this._receiveStreamChunk, this);
  }

  get name(): string {
    return 'JupyterAI';
  }

  async fetch(
    request: CompletionHandler.IRequest,
    context: IInlineCompletionContext
  ): Promise<IInlineCompletionList<IInlineCompletionItem>> {
    const allowedTriggerKind = this._settings.triggerKind;
    const triggerKind = context.triggerKind;
    if (
      allowedTriggerKind === 'manual' &&
      triggerKind !== InlineCompletionTriggerKind.Invoke
    ) {
      // Short-circuit if user requested to only invoke inline completions
      // on manual trigger for jupyter-ai. Users may still get completions
      // from other (e.g. less expensive or faster) providers.
      return { items: [] };
    }
    const mime = request.mimeType ?? 'text/plain';
    const language = this.options.languageRegistry.findByMIME(mime);
    if (!language) {
      console.warn(
        `Could not recognise language for ${mime} - cannot complete`
      );
      return { items: [] };
    }
    if (!this.isLanguageEnabled(language?.name)) {
      // Do not offer suggestions if disabled.
      return { items: [] };
    }
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

    const streamPreference = this._settings.streaming;
    const stream =
      streamPreference === 'always'
        ? true
        : streamPreference === 'never'
        ? false
        : context.triggerKind === InlineCompletionTriggerKind.Invoke;

    if (stream) {
      // Reset stream promises handler
      this._streamPromises.clear();
    }
    const result = await this.options.completionHandler.sendMessage({
      path,
      mime,
      prefix: this._prefixFromRequest(request),
      suffix: this._suffixFromRequest(request),
      language: this._resolveLanguage(language),
      number,
      stream,
      cell_id: cellId
    });

    const error = result.error;
    if (error) {
      Notification.emit(`Inline completion failed: ${error.type}`, 'error', {
        autoClose: false,
        actions: [
          {
            label: 'Show Traceback',
            callback: () => {
              showErrorMessage('Inline completion failed on the server side', {
                message: `${error.title}\n${error.traceback}`
              });
            }
          }
        ]
      });
      const items = [
        {
          error: { message: error.title },
          insertText: ''
        }
      ];
      return { items };
    }
    return result.list;
  }

  /**
   * Stream a reply for completion identified by given `token`.
   */
  async *stream(token: string): AsyncGenerator<StreamChunk, void, unknown> {
    let done = false;
    while (!done) {
      const delegate = new PromiseDelegate<StreamChunk>();
      this._streamPromises.set(token, delegate);
      const promise = delegate.promise;
      yield promise;
      done = (await promise).done;
    }
  }

  get schema(): ISettingRegistry.IProperty {
    const knownLanguages = this.options.languageRegistry.getLanguages();
    return {
      properties: {
        triggerKind: {
          title: 'Inline completions trigger',
          type: 'string',
          oneOf: [
            { const: 'any', title: 'Automatic (on typing or invocation)' },
            { const: 'manual', title: 'Only when invoked manually' }
          ],
          description:
            'When to trigger inline completions when using jupyter-ai.'
        },
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
        },
        disabledLanguages: {
          title: 'Disabled languages',
          type: 'array',
          items: {
            type: 'string',
            oneOf: knownLanguages.map(language => {
              return { const: language.name, title: displayName(language) };
            })
          },
          description:
            'Languages for which the completions should not be shown.'
        },
        streaming: {
          title: 'Streaming',
          type: 'string',
          oneOf: [
            { const: 'always', title: 'Always' },
            { const: 'manual', title: 'When invoked manually' },
            { const: 'never', title: 'Never' }
          ],
          description: 'Whether to show suggestions as they are generated'
        }
      },
      default: JaiInlineProvider.DEFAULT_SETTINGS as any
    };
  }

  async configure(settings: { [property: string]: JSONValue }): Promise<void> {
    this._settings = settings as unknown as JaiInlineProvider.ISettings;
    this._settingsChanged.emit();
  }

  isEnabled(): boolean {
    return this._settings.enabled;
  }

  isLanguageEnabled(language: string): boolean {
    return !this._settings.disabledLanguages.includes(language);
  }

  get settingsChanged(): ISignal<JaiInlineProvider, void> {
    return this._settingsChanged;
  }

  /**
   * Process the stream chunk to make it available in the awaiting generator.
   */
  private _receiveStreamChunk(
    _emitter: CompletionWebsocketHandler,
    chunk: StreamChunk
  ) {
    const token = chunk.response.token;
    if (!token) {
      throw Error('Stream chunks must return define `token` in `response`');
    }
    const delegate = this._streamPromises.get(token);
    if (!delegate) {
      console.warn('Unhandled stream chunk');
    } else {
      delegate.resolve(chunk);
      if (chunk.done) {
        this._streamPromises.delete(token);
      }
    }
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

  private _resolveLanguage(language: IEditorLanguage | null) {
    if (!language) {
      return 'plain English';
    }
    if (language.name === 'ipython') {
      return 'python';
    } else if (language.name === 'ipythongfm') {
      return 'markdown';
    }
    return language.name;
  }

  private _settings: JaiInlineProvider.ISettings =
    JaiInlineProvider.DEFAULT_SETTINGS;
  private _settingsChanged = new Signal<JaiInlineProvider, void>(this);

  private _streamPromises: Map<string, PromiseDelegate<StreamChunk>> =
    new Map();
  private _counter = 0;
}

export namespace JaiInlineProvider {
  export const ID = '@jupyterlab/jupyter-ai';

  export interface IOptions {
    completionHandler: CompletionWebsocketHandler;
    languageRegistry: IEditorLanguageRegistry;
  }

  export interface ISettings {
    triggerKind: 'any' | 'manual';
    maxPrefix: number;
    maxSuffix: number;
    debouncerDelay: number;
    enabled: boolean;
    disabledLanguages: string[];
    streaming: 'always' | 'manual' | 'never';
  }

  export const DEFAULT_SETTINGS: ISettings = {
    triggerKind: 'any',
    maxPrefix: 10000,
    maxSuffix: 10000,
    // The debouncer delay handling is implemented upstream in JupyterLab;
    // here we just increase the default from 0, as compared to kernel history
    // the external AI models may have a token cost associated.
    debouncerDelay: 250,
    enabled: false,
    // ipythongfm means "IPython GitHub Flavoured Markdown"
    disabledLanguages: ['ipythongfm'],
    streaming: 'manual'
  };
}
