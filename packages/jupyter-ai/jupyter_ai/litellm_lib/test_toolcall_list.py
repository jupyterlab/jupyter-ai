from litellm.utils import ChatCompletionDeltaToolCall, Function
from .toolcall_list import ToolCallList

class TestToolCallList():

    def test_single_tool_stream(self):
        """
        Asserts this class works against a sample response from Claude running a
        single tool.
        """
        # Setup test
        ID = "toolu_01TzXi4nFJErYThcdhnixn7e"
        toolcall_list = ToolCallList()
        toolcall_list += [ChatCompletionDeltaToolCall(id=ID, function=Function(arguments='', name='ls'), type='function', index=0)]
        toolcall_list += [ChatCompletionDeltaToolCall(id=None, function=Function(arguments='', name=None), type='function', index=0)]
        toolcall_list += [ChatCompletionDeltaToolCall(id=None, function=Function(arguments='{"path', name=None), type='function', index=0)]
        toolcall_list += [ChatCompletionDeltaToolCall(id=None, function=Function(arguments='": "."}', name=None), type='function', index=0)]

        # Verify the resolved list of calls
        resolved_toolcalls = toolcall_list.resolve()
        assert len(resolved_toolcalls) == 1
        assert resolved_toolcalls[0]
    
    def test_two_tool_stream(self):
        """
        Asserts this class works against a sample response from Claude running a
        two tools in parallel.
        """
        # Setup test
        ID_0 = 'toolu_0141FrNfT2LJg6odqbrdmLM6'
        ID_1 = 'toolu_01DKqnaXVcyp1v1ABxhHC5Sg'
        toolcall_list = ToolCallList()
        toolcall_list += [ChatCompletionDeltaToolCall(id=ID_0, function=Function(arguments='', name='ls'), type='function', index=0)]
        toolcall_list += [ChatCompletionDeltaToolCall(id=None, function=Function(arguments='', name=None), type='function', index=0)]
        toolcall_list += [ChatCompletionDeltaToolCall(id=None, function=Function(arguments='{"path": ', name=None), type='function', index=0)]
        toolcall_list += [ChatCompletionDeltaToolCall(id=None, function=Function(arguments='"."}', name=None), type='function', index=0)]
        toolcall_list += [ChatCompletionDeltaToolCall(id=ID_1, function=Function(arguments='', name='bash'), type='function', index=1)]
        toolcall_list += [ChatCompletionDeltaToolCall(id=None, function=Function(arguments='', name=None), type='function', index=1)]
        toolcall_list += [ChatCompletionDeltaToolCall(id=None, function=Function(arguments='{"com', name=None), type='function', index=1)]
        toolcall_list += [ChatCompletionDeltaToolCall(id=None, function=Function(arguments='mand": "ech', name=None), type='function', index=1)]
        toolcall_list += [ChatCompletionDeltaToolCall(id=None, function=Function(arguments='o \'hello\'"}', name=None), type='function', index=1)]

        # Verify the resolved list of calls
        resolved_toolcalls = toolcall_list.resolve()
        assert len(resolved_toolcalls) == 2
        assert resolved_toolcalls[0].id == ID_0
        assert resolved_toolcalls[0].function.name == "ls"
        assert resolved_toolcalls[0].function.arguments == { "path": "." }
        assert resolved_toolcalls[1].id == ID_1
        assert resolved_toolcalls[1].function.name == "bash"
        assert resolved_toolcalls[1].function.arguments == { "command": "echo \'hello\'" }

