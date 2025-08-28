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
    } catch {
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
  };

  export type ListProvidersResponse = {
    providers: ListProvidersEntry[];
  };

  export type ListChatModelsResponse = {
    chat_models: string[];
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

  export type SecretsList = {
    editable_secrets: string[];
    static_secrets: string[];
  };

  export async function listSecrets(): Promise<SecretsList> {
    return requestAPI<SecretsList>('secrets/', {
      method: 'GET'
    });
  }

  export type UpdateSecretsRequest = {
    updated_secrets: Record<string, string>;
  };

  export async function updateSecrets(
    updatedSecrets: Record<string, string | null>
  ): Promise<void> {
    return requestAPI<void>('secrets/', {
      method: 'PUT',
      body: JSON.stringify({
        updated_secrets: updatedSecrets
      })
    });
  }

  export async function deleteSecret(secretName: string): Promise<void> {
    return updateSecrets({ [secretName]: null });
  }

  export async function listChatModels(): Promise<string[]> {
    const response = await requestAPI<ListChatModelsResponse>('models/chat/', {
      method: 'GET'
    });
    return response.chat_models;
  }

  export async function getChatModel(): Promise<string | null> {
    const response = await requestAPI<DescribeConfigResponse>('config/');
    return response.model_provider_id;
  }

  export async function updateChatModel(modelId: string | null): Promise<void> {
    return await updateConfig({
      model_provider_id: modelId
    });
  }

  export async function getCompletionModel(): Promise<string | null> {
    const response = await requestAPI<DescribeConfigResponse>('config/');
    return response.completions_model_provider_id;
  }

  export async function updateCompletionModel(
    modelId: string | null
  ): Promise<void> {
    return await updateConfig({
      completions_model_provider_id: modelId
    });
  }

  export type GetModelParametersResponse = {
    parameters: Record<string, ParameterSchema>;
    parameter_names: string[];
    count: number;
  };

  export type ParameterSchema = {
    type: 'boolean' | 'integer' | 'number' | 'string' | 'array' | 'object';
    description: string;
    min?: number;
    max?: number;
  };

  export async function getModelParameters(
    modelId?: string,
    provider?: string
  ): Promise<GetModelParametersResponse> {
    const params = new URLSearchParams();
    if (modelId) {
      params.append('model', modelId);
    }
    if (provider) {
      params.append('provider', provider);
    }

    const endpoint = `model-parameters${
      params.toString() ? `?${params.toString()}` : ''
    }`;
    return await requestAPI<GetModelParametersResponse>(endpoint);
  }

  export async function saveModelParameters(
    modelId: string,
    parameters: Record<string, any>
  ): Promise<void> {
    await requestAPI<void>('model-parameters', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model_id: modelId,
        parameters: parameters
      })
    });
  }
}
