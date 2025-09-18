from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio

if TYPE_CHECKING:
    from ..tools import Toolkit
    from .toolcall_list import ToolCallList
    from .types import LitellmToolCallOutput


async def run_tools(tool_call_list: ToolCallList, toolkit: Toolkit) -> list[LitellmToolCallOutput]:
    """
    Runs the tools specified in the list of tool calls returned by
    `self.stream_message()`. 
    
    Returns `list[LitellmToolCallOutput]`, a list of output dictionaries of the
    type expected by LiteLLM.

    Each output in the list should be appended directly to the message history
    on the next request made to the LLM.
    """
    tool_calls = tool_call_list.resolve()
    if not len(tool_calls):
        return []

    tool_outputs: list[LitellmToolCallOutput] = []
    for tool_call in tool_calls:
        # Get tool definition from the correct toolkit
        # TODO: validation?
        tool_name = tool_call.function.name
        tool_defn = toolkit.get_tool_unsafe(tool_name)

        # Run tool and store its output
        try:
            output = tool_defn.callable(**tool_call.function.arguments)
            if asyncio.iscoroutine(output):
                output = await output
        except Exception as e:
            output = str(e)

        # Store the tool output in a dictionary accepted by LiteLLM
        output_dict: LitellmToolCallOutput = {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_call.function.name,
            "content": output,
        }
        tool_outputs.append(output_dict)
    
    return tool_outputs
