import { URLExt } from '@jupyterlab/coreutils';

import { ServerConnection } from '@jupyterlab/services';

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

export namespace AiService {
  /**
   * The instantiation options for a data registry handler.
   */
  export interface IOptions {
    serverSettings?: ServerConnection.ISettings;
  }

  export interface IPromptRequest {
    task_id: string;
    engine_id: string;
    prompt_variables: {
      body: string;
      [key: string]: string;
    };
  }

  export type ChatRequest = {
    prompt: string;
  };

  export type Collaborator = {
    username: string;
    initials: string;
    name: string;
    display_name: string;
    color?: string;
    avatar_url?: string;
  };

  export type ChatClient = Collaborator & {
    id: string;
  };

  export type AgentChatMessage = {
    type: 'agent';
    id: string;
    time: number;
    body: string;
    reply_to: string;
  };

  export type HumanChatMessage = {
    type: 'human';
    id: string;
    time: number;
    body: string;
    client: ChatClient;
  };

  export type ConnectionMessage = {
    type: 'connection';
    client_id: string;
  };

  export type ClearMessage = {
    type: 'clear'
  }

  export type ChatMessage = AgentChatMessage | HumanChatMessage;
  export type Message = AgentChatMessage | HumanChatMessage | ConnectionMessage | ClearMessage;

  export type ChatHistory = {
    messages: ChatMessage[];
  };

  export interface IPromptResponse {
    output: string;
    insertion_mode: 'above' | 'below' | 'replace';
  }

  export async function sendPrompt(
    request: IPromptRequest
  ): Promise<IPromptResponse> {
    let data;

    try {
      data = await requestAPI('prompt', {
        method: 'POST',
        body: JSON.stringify(request)
      });
    } catch (e) {
      return Promise.reject(e);
    }
    return data as IPromptResponse;
  }

  export type ListTasksEntry = {
    id: string;
    name: string;
  };

  export type ListTasksResponse = {
    tasks: ListTasksEntry[];
  };

  export async function listTasks(): Promise<ListTasksResponse> {
    return requestAPI<ListTasksResponse>('tasks');
  }

  export type ListEnginesEntry = {
    id: string;
    name: string;
  };

  export type DescribeTaskResponse = {
    name: string;
    insertion_mode: string;
    prompt_template: string;
    engines: ListEnginesEntry[];
  };

  export async function describeTask(
    id: string
  ): Promise<DescribeTaskResponse> {
    return requestAPI<DescribeTaskResponse>(`tasks/${id}`);
  }
}
