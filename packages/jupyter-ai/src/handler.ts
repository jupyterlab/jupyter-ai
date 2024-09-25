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

  export type CellError = {
    name: string;
    value: string;
    traceback: string[];
  };

  export type TextSelection = {
    type: 'text';
    source: string;
  };

  export type CellSelection = {
    type: 'cell';
    source: string;
  };

  export type CellWithErrorSelection = {
    type: 'cell-with-error';
    source: string;
    error: CellError;
  };

  export type Selection =
    | TextSelection
    | CellSelection
    | CellWithErrorSelection;

  export type ChatRequest = {
    prompt: string;
    selection?: Selection;
  };

  export type ClearRequest = {
    type: 'clear';
    target?: string;
    after?: boolean;
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

  export type Persona = {
    name: string;
    avatar_route: string;
  };

  export type AgentChatMessage = {
    type: 'agent';
    id: string;
    time: number;
    body: string;
    reply_to: string;
    persona: Persona;
    metadata: Record<string, any>;
  };

  export type HumanChatMessage = {
    type: 'human';
    id: string;
    time: number;
    /**
     * The formatted body of the message to be rendered in the UI. Includes both
     * `prompt` and `selection`.
     */
    body: string;
    /**
     * The prompt typed into the chat input by the user.
     */
    prompt: string;
    /**
     * The selection included with the prompt, if any.
     */
    selection?: Selection;
    client: ChatClient;
  };

  export type ConnectionMessage = {
    type: 'connection';
    client_id: string;
    history: ChatHistory;
  };

  export type ClearMessage = {
    type: 'clear';
    targets?: string[];
  };

  export type PendingMessage = {
    type: 'pending';
    id: string;
    time: number;
    body: string;
    reply_to: string;
    persona: Persona;
    ellipsis: boolean;
  };

  export type ClosePendingMessage = {
    type: 'close-pending';
    id: string;
  };

  export type AgentStreamMessage = Omit<AgentChatMessage, 'type'> & {
    type: 'agent-stream';
    complete: boolean;
  };

  export type AgentStreamChunkMessage = {
    type: 'agent-stream-chunk';
    id: string;
    content: string;
    stream_complete: boolean;
    metadata: Record<string, any>;
  };

  export type Request = ChatRequest | ClearRequest;

  export type ChatMessage =
    | AgentChatMessage
    | HumanChatMessage
    | AgentStreamMessage;

  export type Message =
    | AgentChatMessage
    | HumanChatMessage
    | ConnectionMessage
    | ClearMessage
    | PendingMessage
    | ClosePendingMessage
    | AgentStreamMessage
    | AgentStreamChunkMessage;

  export type ChatHistory = {
    messages: ChatMessage[];
    pending_messages: PendingMessage[];
  };

  export type DescribeConfigResponse = {
    model_provider_id: string | null;
    embeddings_provider_id: string | null;
    api_keys: string[];
    send_with_shift_enter: boolean;
    fields: Record<string, Record<string, any>>;
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

  export type ListSlashCommandsEntry = {
    slash_id: string;
    description: string;
  };

  export type ListSlashCommandsResponse = {
    slash_commands: ListSlashCommandsEntry[];
  };

  export async function listSlashCommands(): Promise<ListSlashCommandsResponse> {
    return requestAPI<ListSlashCommandsResponse>('chats/slash_commands');
  }

  export type AutocompleteOption = {
    id: string;
    description: string;
    label: string;
    only_start: boolean;
  };

  export type ListAutocompleteOptionsResponse = {
    options: AutocompleteOption[];
  };

  export async function listAutocompleteOptions(): Promise<ListAutocompleteOptionsResponse> {
    return requestAPI<ListAutocompleteOptionsResponse>(
      'chats/autocomplete_options'
    );
  }

  export async function listAutocompleteArgOptions(
    partialCommand: string
  ): Promise<ListAutocompleteOptionsResponse> {
    return requestAPI<ListAutocompleteOptionsResponse>(
      'chats/autocomplete_options?partialCommand=' +
        encodeURIComponent(partialCommand)
    );
  }
}
