from typing import Any, Dict, List, Literal, Optional, Union

from jupyter_ai_magics import Persona
from jupyter_ai_magics.providers import AuthStrategy, Field
from langchain.pydantic_v1 import BaseModel, validator

DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 100


class CellError(BaseModel):
    name: str
    value: str
    traceback: List[str]


class TextSelection(BaseModel):
    type: Literal["text"] = "text"
    source: str


class CellSelection(BaseModel):
    type: Literal["cell"] = "cell"
    source: str


class CellWithErrorSelection(BaseModel):
    type: Literal["cell-with-error"] = "cell-with-error"
    source: str
    error: CellError


Selection = Union[TextSelection, CellSelection, CellWithErrorSelection]


# the type of message used to chat with the agent
class ChatRequest(BaseModel):
    prompt: str
    selection: Optional[Selection]


class ClearRequest(BaseModel):
    type: Literal["clear"]
    target: Optional[str]
    """
    Message ID of the HumanChatMessage to delete an exchange at.
    If not provided, this requests the backend to clear all messages.
    """

    after: Optional[bool]
    """
    Whether to clear target and all subsequent exchanges.
    """


class ChatUser(BaseModel):
    # User ID assigned by IdentityProvider.
    username: str
    initials: str
    name: str
    display_name: str
    color: Optional[str]
    avatar_url: Optional[str]


class ChatClient(ChatUser):
    # A unique client ID assigned to identify different JupyterLab clients on
    # the same device (i.e. running on multiple tabs/windows), which may have
    # the same username assigned to them by the IdentityProvider.
    id: str


class BaseAgentMessage(BaseModel):
    id: str
    time: float
    body: str

    reply_to: str
    """
    Message ID of the HumanChatMessage being replied to. This is set to an empty
    string if not applicable.
    """

    persona: Persona
    """
    The persona of the selected provider. If the selected provider is `None`,
    this defaults to a description of `JupyternautPersona`.
    """

    metadata: Dict[str, Any] = {}
    """
    Message metadata set by a provider after fully processing an input. The
    contents of this dictionary are provider-dependent, and can be any
    dictionary with string keys. This field is not to be displayed directly to
    the user, and is intended solely for developer purposes.
    """


class AgentChatMessage(BaseAgentMessage):
    type: Literal["agent"] = "agent"


class AgentStreamMessage(BaseAgentMessage):
    type: Literal["agent-stream"] = "agent-stream"
    complete: bool
    # other attrs inherited from `AgentChatMessage`


class AgentStreamChunkMessage(BaseModel):
    type: Literal["agent-stream-chunk"] = "agent-stream-chunk"
    id: str
    """ID of the parent `AgentStreamMessage`."""
    content: str
    """The string to append to the `AgentStreamMessage` referenced by `id`."""
    stream_complete: bool
    """Indicates whether this chunk completes the stream referenced by `id`."""
    metadata: Dict[str, Any] = {}
    """
    The metadata of the stream referenced by `id`. Metadata from the latest
    chunk should override any metadata from previous chunks. See the docstring
    on `BaseAgentMessage.metadata` for information.
    """


class HumanChatMessage(BaseModel):
    type: Literal["human"] = "human"
    id: str
    time: float
    body: str
    """The formatted body of the message to be rendered in the UI. Includes both
    `prompt` and `selection`."""
    prompt: str
    """The prompt typed into the chat input by the user."""
    selection: Optional[Selection]
    """The selection included with the prompt, if any."""
    client: ChatClient


class ClearMessage(BaseModel):
    type: Literal["clear"] = "clear"
    targets: Optional[List[str]] = None
    """
    Message IDs of the HumanChatMessage to delete an exchange at.
    If not provided, this instructs the frontend to clear all messages.
    """


class PendingMessage(BaseModel):
    type: Literal["pending"] = "pending"
    id: str
    time: float
    body: str
    reply_to: str
    persona: Persona
    ellipsis: bool = True
    closed: bool = False


class ClosePendingMessage(BaseModel):
    type: Literal["close-pending"] = "close-pending"
    id: str


# the type of messages being broadcast to clients
ChatMessage = Union[
    AgentChatMessage, HumanChatMessage, AgentStreamMessage, AgentStreamChunkMessage
]


class ChatHistory(BaseModel):
    """History of chat messages"""

    messages: List[ChatMessage]
    pending_messages: List[PendingMessage]


class ConnectionMessage(BaseModel):
    type: Literal["connection"] = "connection"
    client_id: str
    history: ChatHistory


Message = Union[
    ChatMessage,
    ConnectionMessage,
    ClearMessage,
    PendingMessage,
    ClosePendingMessage,
]


class ListProvidersEntry(BaseModel):
    """Model provider with supported models
    and provider's authentication strategy
    """

    id: str
    name: str
    model_id_label: Optional[str]
    models: List[str]
    help: Optional[str]
    auth_strategy: AuthStrategy
    registry: bool
    fields: List[Field]
    chat_models: Optional[List[str]]
    completion_models: Optional[List[str]]


class ListProvidersResponse(BaseModel):
    providers: List[ListProvidersEntry]


class IndexedDir(BaseModel):
    path: str
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP


class IndexMetadata(BaseModel):
    dirs: List[IndexedDir]


class DescribeConfigResponse(BaseModel):
    model_provider_id: Optional[str]
    embeddings_provider_id: Optional[str]
    send_with_shift_enter: bool
    fields: Dict[str, Dict[str, Any]]
    # when sending config over REST API, do not include values of the API keys,
    # just the names.
    api_keys: List[str]
    # timestamp indicating when the configuration file was last read. should be
    # passed to the subsequent UpdateConfig request.
    last_read: int
    completions_model_provider_id: Optional[str]
    completions_fields: Dict[str, Dict[str, Any]]


def forbid_none(cls, v):
    assert v is not None, "size may not be None"
    return v


class UpdateConfigRequest(BaseModel):
    model_provider_id: Optional[str]
    embeddings_provider_id: Optional[str]
    send_with_shift_enter: Optional[bool]
    api_keys: Optional[Dict[str, str]]
    fields: Optional[Dict[str, Dict[str, Any]]]
    # if passed, this will raise an Error if the config was written to after the
    # time specified by `last_read` to prevent write-write conflicts.
    last_read: Optional[int]
    completions_model_provider_id: Optional[str]
    completions_fields: Optional[Dict[str, Dict[str, Any]]]

    _validate_send_wse = validator("send_with_shift_enter", allow_reuse=True)(
        forbid_none
    )
    _validate_api_keys = validator("api_keys", allow_reuse=True)(forbid_none)
    _validate_fields = validator("fields", allow_reuse=True)(forbid_none)


class GlobalConfig(BaseModel):
    """Model used to represent the config by ConfigManager. This is exclusive to
    the backend and should never be sent to the client."""

    model_provider_id: Optional[str]
    embeddings_provider_id: Optional[str]
    send_with_shift_enter: bool
    fields: Dict[str, Dict[str, Any]]
    api_keys: Dict[str, str]
    completions_model_provider_id: Optional[str]
    completions_fields: Dict[str, Dict[str, Any]]


class ListSlashCommandsEntry(BaseModel):
    slash_id: str
    description: str


class ListSlashCommandsResponse(BaseModel):
    slash_commands: List[ListSlashCommandsEntry] = []


class ListOptionsEntry(BaseModel):
    id: str
    """ID of the autocomplete option.
    Includes the command prefix. E.g. "/clear", "@file"."""
    label: str
    """Text that will be inserted into the prompt when the option is selected.
    Includes a space at the end if the option is complete.
    Partial suggestions do not include the space and may trigger future suggestions."""
    description: str
    """Text next to the option in the autocomplete list."""
    only_start: bool
    """Whether to command can only be inserted at the start of the prompt."""


class ListOptionsResponse(BaseModel):
    options: List[ListOptionsEntry] = []
