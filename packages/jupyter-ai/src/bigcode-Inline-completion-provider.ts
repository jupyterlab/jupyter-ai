import {
  CompletionHandler,
  HistoryInlineCompletionProvider,
  IInlineCompletionContext,
  IInlineCompletionItem,
  IInlineCompletionList,
  IInlineCompletionProvider
} from '@jupyterlab/completer';
import { NotebookPanel } from '@jupyterlab/notebook';
import { nullTranslator, TranslationBundle } from '@jupyterlab/translation';
import { retrieveNotebookContentUntilCursor } from './utils/cell-context';

import bigcodeRequestInstance from './utils/bigcode-request';
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
    insertText: string;
    cellCode: string;
  } = {
    insertText: '',
    cellCode: ''
  };
  private _requesting = false;
  private _streamStop = false;
  private _finish = false;
  private _timeoutId: number | null = null;
  private _callCounter = 0;

  get finish(): boolean {
    return this._finish;
  }

  get requesting(): boolean {
    return this._requesting;
  }

  constructor(protected options: HistoryInlineCompletionProvider.IOptions) {
    const translator = options.translator || nullTranslator;
    this._trans = translator.load('jupyterlab');
  }

  get name(): string {
    return this._trans.__('Bigcode');
  }

  shouldClearStateAndPerformAutoRequest(addedString: string): {
    shouldClearState: boolean;
    shouldAutoRequest: boolean;
  } {
    if (this._lastRequestInfo.cellCode === '') {
      return { shouldClearState: false, shouldAutoRequest: true };
    }

    if (addedString.length <= 5) {
      return { shouldClearState: false, shouldAutoRequest: false };
    }

    const previousInsertText = this._lastRequestInfo.insertText;

    let diffPosition = 0;
    while (
      diffPosition < addedString.length &&
      previousInsertText[diffPosition] === addedString[diffPosition]
    ) {
      diffPosition++;
    }

    const shouldClearState =
      previousInsertText.length - diffPosition >=
      addedString.length - diffPosition + 4;

    return {
      shouldClearState: shouldClearState,
      shouldAutoRequest: shouldClearState
    };
  }

  constructContinuationPrompt(context: IInlineCompletionContext): string {
    if (context.widget instanceof NotebookPanel) {
      const widget = context.widget as NotebookPanel;
      const notebookCellContent = retrieveNotebookContentUntilCursor(widget);

      bigcodeRequestInstance.constructContinuationPrompt(notebookCellContent);
      return bigcodeRequestInstance.prompt;
    }

    return '';
  }

  async shortCutHandler(
    request: CompletionHandler.IRequest,
    context: IInlineCompletionContext
  ): Promise<IInlineCompletionList<IInlineCompletionItem>> {
    const items: IInlineCompletionItem[] = [];
    const prompt = this.constructContinuationPrompt(context);

    if (prompt) {
      this.setRequestFinish(true);
      this._lastRequestInfo = {
        insertText: '',
        cellCode: request.text.slice(0, request.offset)
      };
      items.push({
        token: prompt,
        isIncomplete: true,
        insertText: ''
      });
    }

    return { items };
  }

  async autoCompletionHandler(
    request: CompletionHandler.IRequest,
    context: IInlineCompletionContext
  ): Promise<IInlineCompletionList<IInlineCompletionItem>> {
    console.debug('autoCompletionHandler');
    this._streamStop = true;

    const lastRoundCellCodeText = this._lastRequestInfo.cellCode;
    const currentRoundCellCodeText = request.text.slice(0, request.offset);

    const newAddedCodeText = currentRoundCellCodeText.replace(
      lastRoundCellCodeText,
      ''
    );

    const items: IInlineCompletionItem[] = [];
    if (this._lastRequestInfo.insertText.startsWith(newAddedCodeText)) {
      items.push({
        isIncomplete: false,
        insertText: this._lastRequestInfo.insertText.replace(
          newAddedCodeText,
          ''
        )
      });
      return { items };
    } else {
      const { shouldClearState, shouldAutoRequest } =
        this.shouldClearStateAndPerformAutoRequest(newAddedCodeText);

      if (shouldClearState) {
        this.clearState();
      }

      if (shouldAutoRequest) {
        const prompt = this.constructContinuationPrompt(context);
        if (!prompt) {
          return { items: [] };
        }

        const result = await this.simulateSingleRequest(prompt);

        if (result === '<debounce>') {
          return { items: [] };
        } else {
          this._lastRequestInfo = {
            insertText: result,
            cellCode: currentRoundCellCodeText
          };

          this.setRequestFinish(false);

          return {
            items: [
              {
                isIncomplete: false,
                insertText: result
              }
            ]
          };
        }
      }
    }

    this._requesting = false;
    return { items };
  }

  async fetch(
    request: CompletionHandler.IRequest,
    context: IInlineCompletionContext
  ): Promise<IInlineCompletionList<IInlineCompletionItem>> {
    if (!CodeCompletionContextStore.enableCodeCompletion) {
      return { items: [] };
    }

    if (!CodeCompletionContextStore.accessToken) {
      alert('Huggingface Access Token not set.');
      return { items: [] };
    }

    if (context.triggerKind === 1) {
      return await this.autoCompletionHandler(request, context);
    }

    if (context.triggerKind === 0) {
      return await this.shortCutHandler(request, context);
    }

    return { items: [] };
  }

  setRequestFinish(error: boolean): void {
    this._requesting = false;
    this._streamStop = false;
    this._finish = !error;
  }

  clearState(): void {
    this._streamStop = true;
    this._finish = false;
    this._requesting = false;
    this._lastRequestInfo = {
      insertText: '',
      cellCode: ''
    };
  }

  delay = async (ms: number): Promise<void> =>
    new Promise(resolve => setTimeout(resolve, ms));

  simulateSingleRequest(prompt: string): Promise<string> {
    this._callCounter++;

    if (this._requesting) {
      return Promise.resolve('<debounce>');
    }

    if (this._timeoutId) {
      clearTimeout(this._timeoutId);
      this._timeoutId = null;
    }

    const currentCallCount = this._callCounter;

    return new Promise(resolve => {
      this._timeoutId = setTimeout(() => {
        if (this._callCounter === currentCallCount && !this._requesting) {
          this._callCounter = 0;
          this._requesting = true;
          resolve('"""This is the result of a simulated automatic request"""');
          this._timeoutId = null;
        } else {
          resolve('<debounce>');
        }
      }, 2000);
    });
  }

  async *stream(
    token: string
  ): AsyncGenerator<{ response: IInlineCompletionItem }, undefined, unknown> {
    const testResultText =
      '_world():\n    print("Hello World!")\nhello_world()';
    this._requesting = true;
    for (let i = 1; i <= testResultText.length; i++) {
      await this.delay(25);

      if (this._streamStop) {
        console.debug('_streamStop');
        this.setRequestFinish(false);

        yield {
          response: {
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
  //     reponseData = await BigcodeInstance.fetchStream();
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

  //     if (done || this._streamStop) {
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
