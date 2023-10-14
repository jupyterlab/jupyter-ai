import {
  CompletionHandler,
  HistoryInlineCompletionProvider,
  // ICompletionContext,
  IInlineCompletionContext,
  IInlineCompletionItem,
  IInlineCompletionList,
  IInlineCompletionProvider
} from '@jupyterlab/completer';
import { NotebookPanel } from '@jupyterlab/notebook';
import { nullTranslator, TranslationBundle } from '@jupyterlab/translation';
import { getNotebookContentCursor } from './utils/cell-context';
import { constructContinuationPrompt } from './utils/bigcode-request';
// import { sendToBigCodeStream } from './utils/bigcode-request';
import CodeCompletionContextStore from './contexts/code-completion-context-store';

// type BigCodeStream = {
//   token: {
//     id: number;
//     text: string;
//     logprob: number;
//     special: boolean;
//   };
//   generated_text: string | null;
//   details: null;
// };

export class BigcodeInlineCompletionProvider
  implements IInlineCompletionProvider
{
  readonly identifier = '@jupyterlab/inline-completer:bigcode';
  private _trans: TranslationBundle;
  private _lastRequestInfo: {
    prompt: string;
    insertText: string;
    cellCode: string;
  } = {
    prompt: '',
    insertText: '',
    cellCode: ''
  };
  private _requesting = false;
  private _stop = false;
  private _finish = false;

  get finish(): boolean {
    return this._finish;
  }

  set finish(val: boolean) {
    this._finish = val;
  }

  get stop(): boolean {
    return this._stop;
  }

  set stop(val: boolean) {
    this._stop = val;
  }

  get requesting(): boolean {
    return this._requesting;
  }

  set requesting(val: boolean) {
    this._requesting = val;
  }

  constructor(protected options: HistoryInlineCompletionProvider.IOptions) {
    const translator = options.translator || nullTranslator;
    this._trans = translator.load('jupyterlab');
  }

  get name(): string {
    return this._trans.__('Bigcode');
  }

  async fetch(
    request: CompletionHandler.IRequest,
    context: IInlineCompletionContext
  ): Promise<IInlineCompletionList<IInlineCompletionItem>> {
    console.debug('context.triggerKind', context.triggerKind);
    if (!CodeCompletionContextStore.enableCodeCompletion) {
      return { items: [] };
    }

    if (context.triggerKind !== 0) {
      console.debug('this._requesting && context.triggerKind === 0');
      this._stop = true;
      const lastRoundCellCodeText = this._lastRequestInfo.cellCode;
      const currentRoundCellCodeText = request.text;
      const newAddedCodeText = currentRoundCellCodeText.replace(
        lastRoundCellCodeText,
        ''
      );
      if (this._lastRequestInfo.insertText.startsWith(newAddedCodeText)) {
        return {
          items: [
            {
              token: this._lastRequestInfo.prompt,
              isIncomplete: false,
              insertText: this._lastRequestInfo.insertText.replace(
                newAddedCodeText,
                ''
              )
            }
          ]
        };
      } else {
        this.setRequestFinish(false);
        return {
          items: []
        };
      }
    }

    if (!CodeCompletionContextStore.accessToken) {
      alert('Huggingface Access Token not set.');
      return { items: [] };
    }

    const items: IInlineCompletionItem[] = [];
    if (context.widget instanceof NotebookPanel) {
      const widget = context.widget as NotebookPanel;
      const notebookCellContent = getNotebookContentCursor(widget);
      const prompt = constructContinuationPrompt(notebookCellContent, 20);

      if (!prompt) {
        return {
          items: []
        };
      }
      this.setRequestFinish(true);
      this._lastRequestInfo = {
        prompt,
        insertText: '',
        cellCode: request.text
      };
      items.push({
        token: prompt,
        isIncomplete: true,
        insertText: ''
      });
    }
    return { items };
  }

  setRequestFinish(error: boolean): void {
    this._requesting = false;
    this._stop = false;
    this._finish = !error;
  }

  accept(): void {
    this._stop = true;
    this._finish = false;
    this._requesting = false;
    this._lastRequestInfo = {
      prompt: '',
      insertText: '',
      cellCode: ''
    };
  }

  async *stream(
    token: string
  ): AsyncGenerator<{ response: IInlineCompletionItem }, undefined, unknown> {
    const delay = (ms: number) =>
      new Promise(resolve => setTimeout(resolve, ms));
    const testResultText =
      'print("Hello World")\nhello_world()\n    print("Hello World")\nhello_world()\n    print("Hello World")\nhello_world()\n    print("Hello World")\nhello_world()';
    this._requesting = true;
    for (let i = 1; i < testResultText.length - 1; i++) {
      await delay(25);

      if (this._stop) {
        console.debug('_stop');
        this.setRequestFinish(false);
        yield {
          response: {
            token,
            isIncomplete: false,
            insertText: this._lastRequestInfo.insertText
          }
        };
        return;
      }

      const insertChar = testResultText.slice(i - 1, i);
      this._lastRequestInfo.insertText += insertChar;

      yield {
        response: {
          token,
          isIncomplete: i !== testResultText.length - 1,
          insertText: this._lastRequestInfo.insertText
        }
      };
    }

    this.setRequestFinish(false);
  }

  // async *stream(
  //   token: string
  // ): AsyncGenerator<{ response: IInlineCompletionItem }, undefined, unknown> {
  //   if (token === '' || this._requesting) {
  //     return;
  //   }

  //   this._requesting = true;
  //   this._finish = false;
  //   let reponseData: ReadableStream<Uint8Array> | null = null;

  //   try {
  //     reponseData = await sendToBigCodeStream(
  //       token,
  //       CodeCompletionContextStore.maxResponseToken
  //     );
  //   } catch {
  //     yield {
  //       response: {
  //         isIncomplete: false,
  //         insertText: ''
  //       }
  //     };
  //     this.setRequestFinish(true);
  //     return;
  //   }

  //   const decoder = new TextDecoder();
  //   const reader = reponseData.getReader();

  //   while (true) {
  //     const { value, done } = await reader.read();

  //     if (done || this._stop) {
  //       this.setRequestFinish(false);
  //       break;
  //     }

  //     const strValue = decoder.decode(value, { stream: true });

  //     const jsonStrList = strValue.split('data:');

  //     for (const chunk of jsonStrList) {
  //       if (chunk !== '') {
  //         const chunkData = JSON.parse(chunk) as BigCodeStream;
  //         const done = chunkData.token.special;

  //         if (done) {
  //           this.setRequestFinish(false);
  //         } else {
  //           this._lastRequestInfo.insertText += chunkData.token.text;
  //         }

  //         yield {
  //           response: {
  //             isIncomplete: !chunkData.token.special,
  //             insertText: this._lastRequestInfo.insertText
  //           }
  //         };
  //       }
  //     }
  //   }
  // }
}
