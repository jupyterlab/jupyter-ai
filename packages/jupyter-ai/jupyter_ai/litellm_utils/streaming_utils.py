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
