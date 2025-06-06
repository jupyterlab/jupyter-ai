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

  export type DescribeConfigResponse = {
    model_provider_id: string | null;
    embeddings_provider_id: string | null;
    api_keys: string[];
    send_with_shift_enter: boolean;
    fields: Record<string, Record<string, any>>;
    embeddings_fields: Record<string, Record<string, any>>;
    completions_fields: Record<string, Record<string, any>>;
    last_read: number;
    completions_model_provider_id: string | null;
  };

  export type UpdateConfigRequest = {
    model_provider_id?: string | null;
    embeddings_provider_id?: string | null;
    api_keys?: Record<string, string>;
    send_with_shift_enter?: boolean;
    fields?: Record<string, Record<string, any>>;
    last_read?: number;
    completions_model_provider_id?: string | null;
    completions_fields?: Record<string, Record<string, any>>;
    embeddings_fields?: Record<string, Record<string, any>>;
  };

  export async function getConfig(): Promise<DescribeConfigResponse> {
    return requestAPI<DescribeConfigResponse>('config');
  }

  export type EnvAuthStrategy = {
    type: 'env';
    name: string;
  };

  export type AwsAuthStrategy = {
    type: 'aws';
  };

  export type MultiEnvAuthStrategy = {
    type: 'multienv';
    names: string[];
  };

  export type AuthStrategy =
    | AwsAuthStrategy
    | EnvAuthStrategy
    | MultiEnvAuthStrategy
    | null;

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

  export type IntegerField = {
    type: 'integer';
    key: string;
    label: string;
  };

  export type Field = TextField | MultilineTextField | IntegerField;

  export type ListProvidersEntry = {
    id: string;
    name: string;
    model_id_label?: string;
    models: string[];
    help?: string;
    auth_strategy: AuthStrategy;
    registry: boolean;
    completion_models: string[];
    chat_models: string[];
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

  export async function deleteApiKey(keyName: string): Promise<void> {
    return requestAPI<void>(`api_keys/${keyName}`, {
      method: 'DELETE'
    });
  }
}
