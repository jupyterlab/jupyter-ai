from pydantic import BaseModel 
from typing import Dict, List, Union, Literal, Optional

class PromptRequest(BaseModel):
    task_id: str
    engine_id: str
    prompt_variables: Dict[str, str]

# the type of message used to chat with the agent
class ChatRequest(BaseModel):
    prompt: str

class ChatClient(BaseModel):
    # Client ID assigned by us. Necessary because different JupyterLab clients
    # on the same device (i.e. running on multiple tabs/windows) may have the
    # same user ID assigned to them by IdentityProvider.
    id: str
    # User ID assigned by IdentityProvider.
    username: str
    initials: str
    name: str
    display_name: str
    color: Optional[str]
    avatar_url: Optional[str]

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

# the type of messages being broadcast to clients
ChatMessage = Union[
    AgentChatMessage,
    HumanChatMessage,
]

Message = Union[
    AgentChatMessage,
    HumanChatMessage,
    ConnectionMessage
]

class ListEnginesEntry(BaseModel):
    id: str
    name: str

class ListTasksEntry(BaseModel):
    id: str
    name: str

class ListTasksResponse(BaseModel):
    tasks: List[ListTasksEntry]

class DescribeTaskResponse(BaseModel):
    name: str
    insertion_mode: str
    prompt_template: str
    engines: List[ListEnginesEntry]

class ChatHistory(BaseModel):
    """History of chat messages"""
    messages: List[ChatMessage]
