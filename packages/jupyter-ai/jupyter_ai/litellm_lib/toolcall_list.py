from litellm.utils import ChatCompletionDeltaToolCall, Function
import json
from pydantic import BaseModel
from typing import Any
from .types import LitellmToolCall, LitellmToolCallOutput, JaiToolCallProps
from jinja2 import Template

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

    arguments: dict[str, Any]
    """
    Arguments to the tool function, as a dictionary.
    """


class ResolvedToolCall(BaseModel):
    """
    A type-safe, parsed representation of
    `litellm.utils.ChatCompletionDeltaToolCall`.
    """

    id: str
    """
    The ID of the tool call.
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

JAI_TOOL_CALL_TEMPLATE = Template("""
{% for props in props_list %}
<jai-tool-call {{props | xmlattr}}>
</jai-tool-call>
{% endfor %}
""".strip())

class ToolCallList(BaseModel):
    """
    A helper object that defines a custom `__iadd__()` method which accepts a
    `tool_call_deltas: list[ChatCompletionDeltaToolCall]` argument. This class
    is used to aggregate the tool call deltas yielded from a LiteLLM response
    stream and produce a list of tool calls.

    After all tool call deltas are added, the `resolve()` method may be called
    to return a list of resolved tool calls.

    Example usage:

    ```py
    tool_call_list = ToolCallList()
    reply_stream = await litellm.acompletion(..., stream=True)
    
    async for chunk in reply_stream:
        tool_call_delta = chunk.choices[0].delta.tool_calls
        tool_call_list += tool_call_delta
    
    tool_calls = tool_call_list.resolve()
    ```
    """

    _aggregate: list[ChatCompletionDeltaToolCall] = []

    def __iadd__(self, other: list[ChatCompletionDeltaToolCall] | None) -> 'ToolCallList':
        """
        Adds a list of tool call deltas to this instance.

        NOTE: This assumes the 'index' attribute on each entry in this list to
        be accurate. If this assumption doesn't hold, we will need to rework the
        logic here.
        """
        if other is None:
            return self

        # Iterate through each delta
        for delta in other:
            # Ensure `self._aggregate` is at least of size `delta.index + 1`
            for i in range(len(self._aggregate), delta.index + 1):
                self._aggregate.append(ChatCompletionDeltaToolCall(
                    function=Function(arguments=""),
                    index=i,
                ))
            
            # Find the corresponding target in the `self._aggregate` and add the
            # delta on top of it. In most cases, the value of aggregate
            # attribute is set as soon as any delta sets it to a non-`None`
            # value. However, `delta.function.arguments` is a string that should
            # be appended to the aggregate value of that attribute.
            target = self._aggregate[delta.index]
            if delta.type:
                target.type = delta.type
            if delta.id:
                target.id = delta.id
            if delta.function.name:
                target.function.name = delta.function.name
            if delta.function.arguments:
                target.function.arguments += delta.function.arguments
        
        return self


    def __add__(self, other: list[ChatCompletionDeltaToolCall] | None) -> 'ToolCallList':
        """
        Alias for `__iadd__()`.
        """
        return self.__iadd__(other)

            
    def resolve(self) -> list[ResolvedToolCall]:
        """
        Returns the aggregated tool calls as `list[ResolvedToolCall]`.

        Raises an exception if any function arguments could not be parsed from
        JSON into a dictionary. This method should only be called after the
        stream completed without errors.
        """
        resolved_toolcalls: list[ResolvedToolCall] = []
        for i, raw_toolcall in enumerate(self._aggregate):
            # Verify entries are at the correct index in the aggregated list
            assert raw_toolcall.index == i

            # Verify each tool call specifies the name of the tool to run.
            #
            # TODO: Check if this may cause a runtime error. The docstring on
            # `litellm.utils.Function` implies that `name` may be `None`.
            assert raw_toolcall.function.name

            # Verify each tool call defines the type of tool it is calling.
            assert raw_toolcall.type is not None

            # Parse the function argument string into a dictionary
            resolved_fn_args = json.loads(raw_toolcall.function.arguments)

            # Add to the returned list
            resolved_fn = ResolvedFunction(
                name=raw_toolcall.function.name,
                arguments=resolved_fn_args
            )
            resolved_toolcall = ResolvedToolCall(
                id=raw_toolcall.id,
                type=raw_toolcall.type,
                index=i,
                function=resolved_fn
            )
            resolved_toolcalls.append(resolved_toolcall)
        
        return resolved_toolcalls
    
    @property
    def complete(self) -> bool:
        for i, tool_call in enumerate(self._aggregate):
            if tool_call.index != i:
                return False
            if not tool_call.function:
                return False
            if not tool_call.function.name:
                return False
            if not tool_call.type:
                return False
            if not tool_call.function.arguments:
                return False
            try:
                json.loads(tool_call.function.arguments)
            except Exception:
                return False

        return True
    
    def as_litellm_tool_calls(self) -> list[LitellmToolCall]:
        """
        Returns the current list of tool calls as a list of dictionaries.
        
        This should be set in the `tool_calls` key in the dictionary of the
        LiteLLM assistant message responsible for dispatching these tool calls.
        """
        return [
            model.model_dump() for model in self._aggregate
        ]

    def render(self, outputs: list[LitellmToolCallOutput] | None = None) -> str:
        """
        Renders this tool call list as a list of `<jai-tool-call>` elements to
        be shown in the chat.
        """
        # Initialize list of props to render into tool call UI elements
        props_list: list[JaiToolCallProps] = []

        # Index all outputs if passed
        outputs_by_id: dict[str, LitellmToolCallOutput] | None = None
        if outputs:
            outputs_by_id = {}
            for output in outputs:
                outputs_by_id[output['tool_call_id']] = output

        for tool_call in self._aggregate:
            # Build the props for each tool call UI element
            props: JaiToolCallProps = {
                'id': tool_call.id,
                'index': tool_call.index,
                'type': tool_call.type,
                'function_name': tool_call.function.name,
                'function_args': tool_call.function.arguments,
            }

            # Add the output if present
            if outputs_by_id and tool_call.id in outputs_by_id:
                output = outputs_by_id[tool_call.id]
                # Make sure to manually convert the dictionary to a JSON string
                # first. Without doing this, Jinja2 will convert a dictionary to
                # JSON using single quotes instead of double quotes, which
                # cannot be parsed by the frontend.
                output = json.dumps(output)
                props['output'] = output

            props_list.append(props)
        
        # Render the tool call UI elements using the Jinja2 template and return
        return JAI_TOOL_CALL_TEMPLATE.render({
            "props_list": props_list
        })

    
    def __len__(self) -> int:
        return len(self._aggregate)
            