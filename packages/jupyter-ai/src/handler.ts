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
    type: 'clear';
  };

  export type ChatMessage = AgentChatMessage | HumanChatMessage;
  export type Message =
    | AgentChatMessage
    | HumanChatMessage
    | ConnectionMessage
    | ClearMessage;

  export type ChatHistory = {
    messages: ChatMessage[];
  };

  export type Config = {
    model_provider_id: string | null;
    embeddings_provider_id: string | null;
    api_keys: Record<string, string>;
    send_with_shift_enter: boolean | null;
    fields: Record<string, Record<string, any>>;
  };

  export type GetConfigResponse = Config;

  export type UpdateConfigRequest = Config;

  export async function getConfig(): Promise<GetConfigResponse> {
    return requestAPI<GetConfigResponse>('config');
  }

  export type EnvAuthStrategy = {
    type: 'env';
    name: string;
  };

  export type AwsAuthStrategy = {
    type: 'aws';
  };

  export type AuthStrategy = EnvAuthStrategy | AwsAuthStrategy | null;

  export type TextField = {
    type: 'text';
    key: string;
    label: string;
    format: string;
  };

  export type MultilineTextField = {
    type: 'text-multiline';
    key: string;
    label: string;
    format: string;
  };

  export type Field = TextField | MultilineTextField;

  export type ListProvidersEntry = {
    id: string;
    name: string;
    models: string[];
    auth_strategy: AuthStrategy;
    registry: boolean;
    fields: Field[];
  };

  export type ListProvidersResponse = {
    providers: ListProvidersEntry[];
  };

  export async function listLmProviders(): Promise<ListProvidersResponse> {
    return requestAPI<ListProvidersResponse>('providers');
  }

  export async function listEmProviders(): Promise<ListProvidersResponse> {
    return requestAPI<ListProvidersResponse>('providers/embeddings');
  }

  export async function updateConfig(
    config: UpdateConfigRequest
  ): Promise<void> {
    return requestAPI<void>('config', {
      method: 'POST',
      body: JSON.stringify(config)
    });
  }
}
