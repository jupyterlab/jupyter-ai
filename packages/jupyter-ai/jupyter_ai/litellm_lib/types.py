from __future__ import annotations
from typing import TypedDict, Literal, Optional


class LitellmToolCall(TypedDict):
    id: str
    type: Literal['function']
    function: str
    index: int

class LitellmMessage(TypedDict):
    role: Literal['assistant', 'user', 'system']
    content: str
    tool_calls: Optional[list[LitellmToolCall]]

class LitellmToolCallOutput(TypedDict):
    tool_call_id: str
    role: Literal['tool']
    name: str
    content: str

class JaiToolCallProps(TypedDict):
    tool_id: str | None

    type: Literal['function'] | None

    index: int | None

    function_name: str | None

    function_args: str | None
    """
    The arguments to the function as a dictionary converted to a JSON string.
    """

    output: str | None
    """
    The `LitellmToolCallOutput` as a JSON string.
    """