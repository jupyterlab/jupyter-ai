import {
  CompletionHandler,
  HistoryInlineCompletionProvider,
  IInlineCompletionContext,
  IInlineCompletionItem,
  IInlineCompletionList,
  IInlineCompletionProvider,
  InlineCompletionTriggerKind
} from '@jupyterlab/completer';
import { NotebookPanel } from '@jupyterlab/notebook';
import { nullTranslator, TranslationBundle } from '@jupyterlab/translation';
import { retrieveNotebookContentUntilCursor } from './utils/cell-context';

import bigcodeRequestInstance, {
  BigCodeServiceStreamResponseItem
} from './utils/bigcode-request';
import CodeCompletionContextStore from './contexts/code-completion-context-store';

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
  private _requestMode: InlineCompletionTriggerKind = 0;
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

  /**
   * If the request ends, need to call this function to write the status for "accept" use
   */
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

  /**
   * Determine whether the request can be made and clear the status of the request
   */
  private shouldClearStateAndPerformAutoRequest(addedString: string): {
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

  // Function that simulates delay
  private delay = async (ms: number): Promise<void> =>
    new Promise(resolve => setTimeout(resolve, ms));

  /**
   * Post-debounce strategy, the last request within the specified time returns <auto_stream>
   */
  private debounceAutoRequest(): Promise<'<auto_stream>' | '<debounce>'> {
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
          resolve('<auto_stream>');
          this._timeoutId = null;
        } else {
          resolve('<debounce>');
        }
      }, 2000);
    });
  }

  // Construct the next prompt
  private constructContinuationPrompt(
    context: IInlineCompletionContext
  ): string {
    if (context.widget instanceof NotebookPanel) {
      const widget = context.widget as NotebookPanel;
      const notebookCellContent = retrieveNotebookContentUntilCursor(widget);

      bigcodeRequestInstance.constructContinuationPrompt(notebookCellContent);
      return bigcodeRequestInstance.prompt;
    }

    return '';
  }

  /**
   * Main function, calls different functions according to context.triggerKind
   */
  async fetch(
    request: CompletionHandler.IRequest,
    context: IInlineCompletionContext
  ): Promise<IInlineCompletionList<IInlineCompletionItem>> {
    if (!CodeCompletionContextStore.enableCodeCompletion) {
      return { items: [] };
    }

    if (
      !CodeCompletionContextStore.accessToken &&
      !CodeCompletionContextStore.enableMockTest
    ) {
      alert('Huggingface Access Token not set.');
      return { items: [] };
    }

    if (context.triggerKind === 1) {
      return await this.autoCompletionHandler(request, context);
    }

    if (context.triggerKind === 0) {
      return await this.shortCutCompletionHandler(request, context);
    }

    return { items: [] };
  }

  private async shortCutCompletionHandler(
    request: CompletionHandler.IRequest,
    context: IInlineCompletionContext
  ): Promise<IInlineCompletionList<IInlineCompletionItem>> {
    const items: IInlineCompletionItem[] = [];
    const prompt = this.constructContinuationPrompt(context);

    if (prompt) {
      this.setRequestFinish(true);
      this._requestMode = 0;
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

  private async autoCompletionHandler(
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
    if (
      this._lastRequestInfo.insertText.startsWith(newAddedCodeText) &&
      newAddedCodeText !== ''
    ) {
      items.push({
        isIncomplete: false,
        insertText: this._lastRequestInfo.insertText.replace(
          newAddedCodeText,
          ''
        )
      });
      return { items };
    } else {
      // Check whether the request can be made and clear the status
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

        // Need to debounce
        const result = await this.debounceAutoRequest();
        if (result === '<debounce>') {
          return { items: [] };
        }

        if (result === '<auto_stream>') {
          this._lastRequestInfo = {
            insertText: '',
            cellCode: currentRoundCellCodeText
          };
          this._requestMode = 1;
          return {
            items: [
              {
                token: prompt,
                isIncomplete: true,
                insertText: ''
              }
            ]
          };
        }
      }
    }

    this._requesting = false;
    return { items };
  }

  async *stream(
    token: string
  ): AsyncGenerator<{ response: IInlineCompletionItem }, undefined, unknown> {
    if (!CodeCompletionContextStore.enableMockTest) {
      yield* this.completionStream(token);
    } else {
      yield* this.mockCompletionStream(token);
    }
  }

  private async *mockCompletionStream(
    token: string
  ): AsyncGenerator<{ response: IInlineCompletionItem }, undefined, unknown> {
    this._requesting = true;

    if (this._requestMode === 0) {
      yield* this.mockKeypressCompletionStream(token);
    } else if (this._requestMode === 1) {
      yield* this.mockAutomaticCompletionStream(token);
    }

    this.setRequestFinish(false);
  }

  private async *mockKeypressCompletionStream(
    token: string
  ): AsyncGenerator<{ response: IInlineCompletionItem }, undefined, unknown> {
    const testResultText =
      '"""This is the first line generated by the mockKeypressCompletionStreamr"""\n    """This is the second line generated by the mockKeypressCompletionStream"""';

    for (let i = 1; i <= testResultText.length; i++) {
      await this.delay(10);

      if (this._streamStop) {
        console.debug('_streamStop');
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
          token: token,
          isIncomplete: i !== testResultText.length - 1,
          insertText: this._lastRequestInfo.insertText
        }
      };
    }
  }

  private async *mockAutomaticCompletionStream(
    token: string
  ): AsyncGenerator<{ response: IInlineCompletionItem }, undefined, unknown> {
    await this.delay(1000);
    const insertText =
      '"""This is the first line that automatically triggers the mockAutomaticCompletionStream"""\n    """This is the second line that automatically triggers the mockAutomaticCompletionStream"""';
    this._lastRequestInfo.insertText = insertText;

    yield {
      response: {
        token,
        isIncomplete: false,
        insertText: insertText
      }
    };
  }

  private async *completionStream(
    token: string
  ): AsyncGenerator<{ response: IInlineCompletionItem }, undefined, unknown> {
    this._requesting = true;

    if (this._requestMode === 0) {
      yield* this.keypressCompletionStream(token);
    } else if (this._requestMode === 1) {
      yield* this.automaticCompletionStream(token);
    }

    this.setRequestFinish(false);
  }

  private async *keypressCompletionStream(
    token: string
  ): AsyncGenerator<{ response: IInlineCompletionItem }, undefined, unknown> {
    if (token === '') {
      return;
    }

    this._requesting = true;
    this._finish = false;
    let reponseData: ReadableStream<Uint8Array> | null = null;

    try {
      reponseData = await bigcodeRequestInstance.fetchStream(true);
    } catch {
      yield {
        response: {
          isIncomplete: false,
          insertText: ''
        }
      };
      this.setRequestFinish(true);
      return;
    }

    const decoder = new TextDecoder();
    const reader = reponseData.getReader();

    while (true) {
      const { value, done } = await reader.read();

      if (done || this._streamStop) {
        return;
      }

      const strValue = decoder.decode(value, { stream: true });

      const jsonStrList = strValue.split('data:');

      for (const chunk of jsonStrList) {
        if (chunk !== '') {
          const chunkData = JSON.parse(
            chunk
          ) as BigCodeServiceStreamResponseItem;
          const done = chunkData.token.special;

          if (!done) {
            this._lastRequestInfo.insertText += chunkData.token.text;
          }

          yield {
            response: {
              isIncomplete: !done,
              insertText: this._lastRequestInfo.insertText
            }
          };
        }
      }
    }
  }

  private async *automaticCompletionStream(
    token: string
  ): AsyncGenerator<{ response: IInlineCompletionItem }, undefined, unknown> {
    try {
      const reponseData = await bigcodeRequestInstance.fetchStream(false);

      yield {
        response: {
          token,
          isIncomplete: false,
          insertText: reponseData[0].generated_text
        }
      };
    } catch {
      return;
    }
  }
}
