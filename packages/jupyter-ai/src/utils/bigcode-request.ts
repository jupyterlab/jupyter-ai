import CodeCompletionContextStore from '../contexts/code-completion-context-store';
import { ICell } from '../types/cell';

/**
 * Generates the appropriate prompt string based on the cell type.
 * The cell type can be either 'code' or 'markdown'.
 *
 * @param {ICell} cell - The cell object which includes the type and content.
 * @returns {string} The generated prompt string for the cell.
 */
const getPromptForCell = (cell: ICell): string => {
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

function countSpaces(str: string) {
  const matches = str.match(/ /g);
  return matches ? matches.length : 0;
}

/**
 * Constructs a continuation prompt based on the provided context.
 * It concatenates the prompts for all the cells in the context.
 *
 * @param {ICell[] | null} context - An array of cells representing the context.
 * @returns {string | null} The constructed continuation prompt or null if context is empty.
 */
export const constructContinuationPrompt = (
  context: ICell[] | null,
  maxTokens: number
): string | null => {
  if (!context || context.length === 0) {
    return null;
  }

  let prompt = '';
  for (let i = context.length - 1; i >= 0; i--) {
    prompt = getPromptForCell(context[i]) + prompt;
    if (countSpaces(prompt) > maxTokens) {
      break;
    }
  }

  return '<start_jupyter>' + prompt;
};

/**
 * Sends the given prompt to the BigCode service for code completion.
 * It requires the BigCode service URL and the Huggingface Access Token to be set in the CodeCompletionContextStore.
 *
 * @param {string | null} prompt - The prompt string to be sent for code completion.
 * @returns {Promise<{ generated_text: string }[]>} A promise that resolves with the generated text or rejects with an error.
 */
export const sendToBigCodeStream = async (
  prompt: string | null,
  max_tokens: number
): Promise<ReadableStream<Uint8Array>> => {
  const { bigcodeUrl } = CodeCompletionContextStore;
  const { accessToken } = CodeCompletionContextStore;

  if (!bigcodeUrl || !accessToken) {
    alert('BigCode service URL or Huggingface Access Token not set.');
    return new Promise((resolve, reject) => {
      reject('BigCode service URL or Huggingface Access Token not set.');
    });
  }

  if (!prompt) {
    return new Promise((resolve, reject) => {
      reject('Prompt is null');
    });
  }

  const bodyData = {
    inputs: prompt,
    stream: false,
    parameters: {
      temperature: 0.01,
      return_full_text: false,
      max_tokens,
      stop: ['<jupyter_output>']
    }
  };

  const response = await fetch(bigcodeUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`
    },
    body: JSON.stringify(bodyData)
  });

  // Check if response status code is in the range 200-299
  if (!response || !response.ok) {
    return new Promise((resolve, reject) => {
      reject(response.json());
    });
  }

  const streamData = response.body;

  if (!streamData) {
    return new Promise((resolve, reject) => {
      reject(response.json());
    });
  }

  return streamData;
};
