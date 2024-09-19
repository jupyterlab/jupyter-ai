import argparse
import ast
import os
from pathlib import Path
from typing import Dict, Literal, Type

import numpy as np
from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from .base import BaseChatHandler, SlashCommandRoutingType

PROMPT_TEMPLATE = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:
Format the answer to be as pretty as possible.
"""
CONDENSE_PROMPT = PromptTemplate.from_template(PROMPT_TEMPLATE)


class ToolsChatHandler(BaseChatHandler):
    """Processes messages prefixed with /tools. This actor will
    bind a <tool_name>.py collection of tools to the LLM and
    build a computational graph to direct queries to tools
    that apply to the prompt. If there is no appropriate tool,
    the LLM will default to a standard chat response from the LLM
    without using tools.
    """

    id = "tools"
    name = "Use tools with LLM"
    help = "Ask a question that uses your custom tools"
    routing_type = SlashCommandRoutingType(slash_id="tools")

    uses_llm = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.parser.prog = "/tools"
        self.parser.add_argument(
            "-t",
            "--tools",
            action="store",
            default=None,
            type=str,
            help="Uses tools in the given file name",
        )
        self.parser.add_argument(
            "-l",
            "--list",
            action="store_true",
            help="Lists available files in tools directory.",
        )

        self.parser.add_argument("query", nargs=argparse.REMAINDER)
        self.tools_file_path = None

    # https://python.langchain.com/v0.2/docs/integrations/platforms/
    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        unified_parameters = {
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        llm = provider(**unified_parameters)
        self.llm = llm
        # self.chat_provider = self.setChatProvider(provider)
        memory = ConversationBufferWindowMemory(
            memory_key="chat_history", return_messages=True, k=2
        )
        self.llm_chain = LLMChain(
            llm=self.llm, prompt=CONDENSE_PROMPT, memory=memory, verbose=False
        )

    # Get required tool files from ``.jupyter/jupyter-ai/tools/``
    def getToolFiles(self) -> list:
        if os.path.isfile(self.tools_file_path):
            file_paths = [self.tools_file_path]
        elif os.path.isdir(self.tools_file_path):
            file_paths = []
            for filename in os.listdir(self.tools_file_path):
                file_paths.append(os.path.join(self.tools_file_path, filename))
        else:
            self.reply("No tools found.")
        return file_paths

    def useLLMwithTools(self, query: str) -> str:
        """
        LangGraph documentation : https://langchain-ai.github.io/langgraph/tutorials/introduction/
        The code below:
        1. Extracts the function names in the custom tools file
        2. Adds the tools to the Tool Node
        3. Binds the Tool Node to the LLM
        4. Sets up a basic LangGraph with nodes and edges
        5. Compiles the graph into a runnable app
        6. This function is then called with a prompt
        Every time a query is submitted the langgraph is rebuilt in case the tools file has been changed.
        """

        # Calls the requisite tool in the LangGraph
        def call_tool(state: MessagesState) -> Dict[str, list]:
            messages = state["messages"]
            response = self.model_with_tools.invoke(messages)
            return {"messages": [response]}

        def conditional_continue(state: MessagesState) -> Literal["tools", "__end__"]:
            messages = state["messages"]
            last_message = messages[-1]
            if last_message.tool_calls:
                return "tools"
            return "__end__"

        # Get all tool objects from the tool files
        def getTools(file_paths):
            if len(file_paths) > 0:
                tool_names = []
                for file_path in file_paths:
                    with open(file_path) as file:
                        exec(file.read())
                    # For each tool file, collect tool list
                    try:
                        with open(file_path) as file:
                            content = file.read()
                            tree = ast.parse(content)
                            tool_list = []
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    for decorator in node.decorator_list:
                                        if (
                                            isinstance(decorator, ast.Name)
                                            and decorator.id == "tool"
                                        ):
                                            tool_list.append(node.name)
                        # return tools  # this is a list
                    except FileNotFoundError as e:  # to do
                        self.reply(f"Tools file not found at {file_path}.")
                        return

                    tool_names = tool_names + tool_list
                tools = [eval(j) for j in tool_names]
                return tools  # a list of function objects
            else:
                self.reply("No available tool files.")

        # Get tool file(s), then tools within tool files, and create tool node from tools
        tool_files = self.getToolFiles()
        tools = getTools(tool_files)
        tool_node = ToolNode(tools)

        # Bind tools to LLM
        # Check if the LLM class takes tools else advise user accordingly.
        # Can be extended to include temperature parameter
        try:
            self.model_with_tools = self.llm.__class__(
                model_id=self.llm.model_id
            ).bind_tools(tools)
        except Exception as e:
            self.reply(f"Not a chat model, cannot be used with tools. {e}")

        # Initialize graph
        agentic_workflow = StateGraph(MessagesState)
        # Define the agent and tool nodes we will cycle between
        agentic_workflow.add_node("agent", call_tool)
        agentic_workflow.add_node("tools", tool_node)
        # Add edges to the graph
        agentic_workflow.add_edge("__start__", "agent")
        agentic_workflow.add_conditional_edges("agent", conditional_continue)
        agentic_workflow.add_edge("tools", "agent")
        # Compile graph
        app = agentic_workflow.compile()

        # Run query
        res = app.invoke({"messages": query})
        return res["messages"][-1].content

    async def process_message(self, message: HumanChatMessage):
        args = self.parse_args(message)
        if args is None:
            return

        if args.list:
            tool_files = os.listdir(
                os.path.join(Path.home(), ".jupyter/jupyter-ai/tools")
            )
            self.reply(f"The available tools files are: {tool_files}")
            return
        elif args.tools:
            self.tools_file_path = os.path.join(
                Path.home(), ".jupyter/jupyter-ai/tools", args.tools
            )
        else:
            self.tools_file_path = os.path.join(
                Path.home(), ".jupyter/jupyter-ai/tools"
            )

        query = " ".join(args.query)
        if not query:
            self.reply(f"{self.parser.format_usage()}", message)
            return

        self.get_llm_chain()

        try:
            with self.pending("Using LLM with tools ..."):
                response = self.useLLMwithTools(query)
                self.reply(response, message)
        except Exception as e:
            self.log.error(e)
            response = """Sorry, tool usage failed.
            Either (i) this LLM does not accept tools, (ii) there an error in
            the custom tools file, (iii) you may also want to check the
            location and name of the tools file, or (iv) you may need to install the
            `langchain_<provider_name>` package. (v) Finally, check that you have
            authorized access to the LLM."""
            self.reply(response, message)
