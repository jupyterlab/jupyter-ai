from typing import Any, Dict, List, Literal, Optional, Union

from jupyter_ai_magics.providers import AuthStrategy, Field
from pydantic import BaseModel

DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 100


# the type of message used to chat with the agent
class ChatRequest(BaseModel):
    prompt: str


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


class AgentChatMessage(BaseModel):
    type: Literal["agent"] = "agent"
    id: str
    time: float
    body: str
    # message ID of the HumanChatMessage it is replying to
    reply_to: str


class HumanChatMessage(BaseModel):
    type: Literal["human"] = "human"
    id: str
    time: float
    body: str
    client: ChatClient


class ConnectionMessage(BaseModel):
    type: Literal["connection"] = "connection"
    client_id: str


class ClearMessage(BaseModel):
    type: Literal["clear"] = "clear"


# the type of messages being broadcast to clients
ChatMessage = Union[
    AgentChatMessage,
    HumanChatMessage,
]

Message = Union[AgentChatMessage, HumanChatMessage, ConnectionMessage, ClearMessage]


class ChatHistory(BaseModel):
    """History of chat messages"""

    messages: List[ChatMessage]


class ListProvidersEntry(BaseModel):
    """Model provider with supported models
    and provider's authentication strategy
    """

    id: str
    name: str
    models: List[str]
    auth_strategy: AuthStrategy
    registry: bool
    fields: List[Field]


class ListProvidersResponse(BaseModel):
    providers: List[ListProvidersEntry]


class IndexedDir(BaseModel):
    path: str
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP


class IndexMetadata(BaseModel):
    dirs: List[IndexedDir]


class GlobalConfig(BaseModel):
    model_provider_id: Optional[str] = None
    embeddings_provider_id: Optional[str] = None
    api_keys: Dict[str, str] = {}
    send_with_shift_enter: Optional[bool] = None
    fields: Dict[str, Dict[str, Any]] = {}
