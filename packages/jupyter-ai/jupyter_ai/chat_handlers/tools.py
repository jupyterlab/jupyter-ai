import argparse
import ast
import os
from pathlib import Path
from typing import Dict, Literal, Type

import numpy as np
from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from jupyter_core.paths import jupyter_config_dir
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import ConfigurableFieldSpec
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from .base import BaseChatHandler, SlashCommandRoutingType

TOOLS_DIR = os.path.join(jupyter_config_dir(), "jupyter-ai", "tools")

PROMPT_TEMPLATE = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:
Format the answer to be as pretty as possible.
"""
CONDENSE_PROMPT = PromptTemplate.from_template(PROMPT_TEMPLATE)


class ExceptionNoToolsFile(Exception):
    """Missing tools file"""

    pass


class ExceptionModelDoesTakeTools(Exception):
    """Model is not a chat model that takes tools"""

    pass


class ExceptionModelNotAuthorized(Exception):
    """Authentication failed for model authorization"""

    pass


class ExceptionNotChatModel(Exception):
    """Not a chat model"""

    pass


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

    def setup_llm(self, provider: Type[BaseProvider], provider_params: Dict[str, str]):
        """Sets up the LLM before creating the LLM Chain"""
        unified_parameters = {
            "verbose": True,
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        llm = provider(**unified_parameters)
        self.llm = llm
        return llm

    # https://python.langchain.com/v0.2/docs/integrations/platforms/'
    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        """Uses the LLM set up to create the LLM Chain"""
        llm = self.setup_llm(provider, provider_params)
        prompt_template = llm.get_chat_prompt_template()
        self.llm = llm

        runnable = prompt_template | llm  # type:ignore
        if not llm.manages_history:
            runnable = RunnableWithMessageHistory(
                runnable=runnable,  #  type:ignore[arg-type]
                get_session_history=self.get_llm_chat_memory,
                input_messages_key="input",
                history_messages_key="history",
                history_factory_config=[
                    ConfigurableFieldSpec(
                        id="last_human_msg",
                        annotation=HumanChatMessage,
                    ),
                ],
            )
        self.llm_chain = runnable

    def get_tool_files(self) -> list:
        """
        Gets required tool files from TOOLS_DIR
        which is the directory in which all tool files are placed.
        """
        try:
            if os.path.isfile(self.tools_file_path):
                file_paths = [self.tools_file_path]
            elif os.path.isdir(self.tools_file_path):
                file_paths = []
                for filename in os.listdir(self.tools_file_path):
                    file_paths.append(os.path.join(self.tools_file_path, filename))
            return file_paths
        except UnboundLocalError as e:
            raise ExceptionNoToolsFile()

    def use_llm_with_tools(self, query: str) -> str:
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

        def call_tool(state: MessagesState) -> Dict[str, list]:
            """Calls the requisite tool in the LangGraph"""
            messages = state["messages"]
            response = self.model_with_tools.invoke(messages)
            return {"messages": [response]}

        def conditional_continue(state: MessagesState) -> Literal["tools", "__end__"]:
            """
            Branches from tool back to the agent or ends the
            computation on the langgraph
            """
            messages = state["messages"]
            last_message = messages[-1]
            if len(last_message.tool_calls)>0:
                return "tools"
            return "__end__"

        def get_tools(file_paths: list):
            """
            Gets all tool objects from the tool files.
            Returns tool objects of functions that have the `@tool` decorator.
            Ignores all code in tool files that does not relate to tool functions.
            """
            if len(file_paths) > 0:
                tools = []  # tool objects
                for file_path in file_paths:
                    try:  # For each tool file, collect tool list and function source code
                        with open(file_path) as file:
                            content = file.read()
                            tree = ast.parse(content)  # Build AST tree
                            for node in ast.walk(
                                tree
                            ):  # Get the nodes with @tool decorator
                                if isinstance(node, ast.FunctionDef):
                                    for decorator in node.decorator_list:
                                        if (
                                            isinstance(decorator, ast.Name)
                                            and decorator.id == "tool"
                                        ):
                                            exec(
                                                ast.unparse(node)
                                            )  # dynamically execute the tool function (object in memory)
                                            tools.append(
                                                eval(node.name)
                                            )  # adds function to tool objects list
                    except FileNotFoundError:
                        raise ExceptionNoToolsFile()
                return tools  # a list of function objects
            else:
                self.reply("No available tool files.")

        # Get tool file(s), then tools within tool files, and create tool node from tools
        tool_files = self.get_tool_files()  # Get all tool files (python modules)
        tools = get_tools(tool_files)  # get tool objects
        tool_node = ToolNode(tools)  # create a LangGraph node with tool objects

        # Bind tools to LLM
        # Check if the LLM class takes tools else advise user accordingly.
        # Can be extended to include temperature parameter
        self.llm = self.setup_llm(
            self.config_manager.lm_provider, self.config_manager.lm_provider_params
        )
        if not self.llm.is_chat_provider:
            raise ExceptionNotChatModel()
        try:
            self.model_with_tools = self.llm.__class__(
                model_id=self.llm.model_id
            ).bind_tools(tools)
        except AttributeError:
            raise ExceptionModelDoesTakeTools()
        except Exception:
            raise ExceptionModelNotAuthorized()

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
            tool_files = os.listdir(os.path.join(Path.home(), TOOLS_DIR))
            self.reply(f"The available tools files are: {tool_files}")
            return
        elif args.tools:
            self.tools_file_path = os.path.join(Path.home(), TOOLS_DIR, args.tools)
        else:
            self.tools_file_path = os.path.join(Path.home(), TOOLS_DIR)

        query = " ".join(args.query)
        if not query:
            self.reply(f"{self.parser.format_usage()}", message)
            return

        self.get_llm_chain()

        try:
            with self.pending("Using LLM with tools ..."):
                response = self.use_llm_with_tools(query)
                self.reply(response, message)
        except ExceptionNoToolsFile:
            self.reply(f"Tools file not found at {self.tools_file_path}.")
        except ExceptionModelDoesTakeTools:
            self.reply(f"Not a chat model that takes tools.")
        except ExceptionModelNotAuthorized:
            self.reply(
                f"API failed. Model not authorized or provider package not installed."
            )
        except ExceptionNotChatModel:
            self.reply(f"Not a chat model, cannot be used with tools.")
        except Exception as e:
            self.log.error(e)
