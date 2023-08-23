import GlobalStore from '../contexts/continue-writing-context';

export const constructContinuationPrompt = (context: string[]): string|null => {
  if (context == null) {
      return null;
  }

  const prompt = '<start_jupyter>' + context.join('\n');
  return prompt;
}

export const sendToBigCode = async (prompt: string | null): Promise<{ generated_text: string }[]> => {
  const { bigcodeUrl } = GlobalStore;
  const { accessToken } = GlobalStore;

  if (!bigcodeUrl || !accessToken) {
    alert('BigCode service URL or Huggingface Access Token not set.');
    return new Promise((resolve, reject) => { reject('BigCode service URL or Huggingface Access Token not set.') });
  }
  if (!prompt) {
    return new Promise((resolve, reject) => { reject('Prompt is null') });
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

export const processCompletionResult = (result: { generated_text: string }[]): string => {
  if (result.length == 0) {
    return ""
  }

  return result[0].generated_text.replace("<jupyter_output>", "")
}