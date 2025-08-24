from pydantic import BaseModel
from .toolcall_list import ToolCallList

class StreamResult(BaseModel):
    id: str
    """
    ID of the new message.
    """

    tool_calls: ToolCallList
    """
    Tool calls requested by the LLM in its streamed response.
    """
