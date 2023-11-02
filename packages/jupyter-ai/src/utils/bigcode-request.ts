import CodeCompletionContextStore, {
  IGlobalStore
} from '../contexts/code-completion-context-store';
import { ICell } from '../types/cell';
import { makeObservable, computed } from 'mobx';

export type BigCodeServiceStreamResponseItem = {
  token: {
    id: number;
    text: string;
    logprob: number;
    special: boolean;
  };
  generated_text: string | null;
  details: null;
};

export type BigCodeServiceNotStreamResponse = {
  generated_text: string;
}[];

class Bigcode {
  spaceCount: number;
  private _prompt: string;

  constructor(private store: IGlobalStore) {
    makeObservable(this);
    this.spaceCount = 0;
    this._prompt = '';
  }

  @computed get bigcodeUrl() {
    return this.store.bigcodeUrl;
  }

  @computed get accessToken() {
    return this.store.accessToken;
  }

  @computed get maxTokens() {
    return this.store.maxPromptToken;
  }

  get prompt() {
    return this._prompt;
  }

  async send(stream: true): Promise<ReadableStream<Uint8Array>>;
  async send(stream: false): Promise<BigCodeServiceNotStreamResponse>;
  async send(
    stream = false
  ): Promise<ReadableStream<Uint8Array> | BigCodeServiceNotStreamResponse> {
    if (!this.bigcodeUrl || !this.accessToken) {
      alert('BigCode service URL or Huggingface Access Token not set.');
      throw new Error(
        'BigCode service URL or Huggingface Access Token not set.'
      );
    }

    if (!this._prompt) {
      throw new Error('Prompt is null');
    }

    const bodyData = {
      inputs: this.prompt,
      stream,
      parameters: {
        temperature: 0.01,
        return_full_text: false,
        max_tokens: this.maxTokens,
        stop: ['<jupyter_output>']
      }
    };

    const response = await fetch(this.bigcodeUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.accessToken}`
      },
      body: JSON.stringify(bodyData)
    });

    if (!response || !response.ok) {
      throw new Error(await response.json());
    }

    const streamData = response.body;

    if (!streamData) {
      throw new Error(await response.json());
    }

    return stream ? streamData : response.json();
  }

  getPromptForCell = (cell: ICell): string => {
    let cellPrompt = '';
    switch (cell.type) {
      case 'code':
        cellPrompt += '<jupyter_code>';
        break;
      case 'markdown':
        cellPrompt += '<jupyter_text>';
        break;
      case 'output':
        cellPrompt += '<jupyter_output>';
        break;
    }
    return cellPrompt + cell.content;
  };

  countSpaces(str: string) {
    const matches = str.match(/ /g);
    this.spaceCount = matches ? matches.length : 0;
  }

  constructContinuationPrompt(context: ICell[] | null) {
    if (!context || context.length === 0) {
      return null;
    }

    let prompt = '';
    for (let i = context.length - 1; i >= 0; i--) {
      prompt = this.getPromptForCell(context[i]) + prompt;
      this.countSpaces(prompt);
      if (this.spaceCount > this.maxTokens) {
        break;
      }
    }
    this._prompt = '<start_jupyter>' + prompt;
  }
}

export default new Bigcode(CodeCompletionContextStore);
