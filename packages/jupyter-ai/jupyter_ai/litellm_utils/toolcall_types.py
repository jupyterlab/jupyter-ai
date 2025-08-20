from __future__ import annotations
from pydantic import BaseModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

class ResolvedFunction(BaseModel):
    """
    A type-safe, parsed representation of `litellm.utils.Function`.
    """

    name: str
    """
    Name of the tool function to be called.

    TODO: Check if this attribute is defined for non-function tools, e.g. tools
    provided by a MCP server. The docstring on `litellm.utils.Function` implies
    that `name` may be `None`.
    """

    arguments: dict
    """
    Arguments to the tool function, as a dictionary.
    """

class ResolvedToolCall(BaseModel):
    """
    A type-safe, parsed representation of
    `litellm.utils.ChatCompletionDeltaToolCall`.
    """

    id: str | None
    """
    The ID of the tool call. This should always be provided by LiteLLM, this
    type is left optional as we do not use this attribute.
    """

    type: str
    """
    The 'type' of tool call. Usually 'function'.

    TODO: Make this a union of string literals to ensure we are handling every
    potential type of tool call.
    """

    function: ResolvedFunction
    """
    The resolved function. See `ResolvedFunction` for more info.
    """

    index: int
    """
    The index of this tool call.

    This is usually 0 unless the LLM supports parallel tool calling.
    """
