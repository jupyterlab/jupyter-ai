from litellm.utils import ChatCompletionDeltaToolCall, Function
import json

from .toolcall_types import ResolvedToolCall, ResolvedFunction

class ToolCallList():
    """
    A helper object that defines a custom `__iadd__()` method which accepts a
    `tool_call_deltas: list[ChatCompletionDeltaToolCall]` argument. This class
    is used to aggregate the tool call deltas yielded from a LiteLLM response
    stream and produce a list of tool calls.

    After all tool call deltas are added, the `process()` method may be called
    to return a list of resolved tool calls.

    Example usage:

    ```py
    tool_call_list = ToolCallList()
    reply_stream = await litellm.acompletion(..., stream=True)
    
    async for chunk in reply_stream:
        tool_call_delta = chunk.choices[0].delta.tool_calls
        tool_call_list += tool_call_delta
    
    tool_call_list.resolve()
    ```
    """

    _aggregate: list[ChatCompletionDeltaToolCall]

    def __init__(self):
        self.size = None
        
        # Initialize `_aggregate`
        self._aggregate = []
    

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
        Resolve the aggregated tool call delta lists into a list of tool calls.
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
            
        
    