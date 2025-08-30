from __future__ import annotations
from pydantic import BaseModel
from .toolcall_list import ToolCallList

class StreamResult(BaseModel):
    id: str
    """
    ID of the new message.
    """

    tool_call_list: ToolCallList
    """
    Tool calls requested by the LLM in its streamed response.
    """

class ToolCallOutput(BaseModel):
    tool_call_id: str
    role: str = "tool"
    name: str
    content: str

