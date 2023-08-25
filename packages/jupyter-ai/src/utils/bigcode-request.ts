import GlobalStore from '../contexts/continue-writing-context';
import { ICell } from '../types/cell';

const getPromptForCell = (cell: ICell): string => {
  let cellPrompt = '';
  switch (cell.type) {
    case 'code':
      cellPrompt += '<jupyter_code>';
      break;
    case 'markdown':
      cellPrompt += '<jupyter_text>';
      break;
  }
  return cellPrompt + cell.content;
};

export const constructContinuationPrompt = (
  context: ICell[] | null
): string | null => {
  if (!context || context.length === 0) {
    return null;
  }

  const prompt = '<start_jupyter>' + context.map(getPromptForCell).join('');

  return prompt;
};

export const sendToBigCode = async (
  prompt: string | null
): Promise<{ generated_text: string }[]> => {
  const { bigcodeUrl } = GlobalStore;
  const { accessToken } = GlobalStore;

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
      stop: ['<jupyter_output>']
    }
  };

  const response = fetch(bigcodeUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`
    },
    body: JSON.stringify(bodyData)
  });

  const data = (await response).json();
  return data;
};

export const processCompletionResult = (
  result: { generated_text: string }[]
): string => {
  if (result.length === 0) {
    return '';
  }

  return result[0].generated_text.replace('<jupyter_output>', '');
};
