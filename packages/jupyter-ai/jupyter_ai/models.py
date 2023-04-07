from pydantic import BaseModel, validator
from typing import Dict, List, Literal

from langchain.schema import BaseMessage, _message_to_dict

class PromptRequest(BaseModel):
    task_id: str
    engine_id: str
    prompt_variables: Dict[str, str]

class ChatRequest(BaseModel):
    prompt: str

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
    messages: List[BaseMessage]

    class Config:
        json_encoders = {
            BaseMessage: lambda v: _message_to_dict(v)
        }