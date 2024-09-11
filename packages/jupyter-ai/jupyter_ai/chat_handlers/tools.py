##### TO DO #####
# - icon for /tools
# - Where to put the mytools.py file?
# - Pass tools file location on startup, or in chat, or keep one file, or handle multiple tool files.
# - Handling the different providers (Chat*) and models (model_id)
# - To integrate with chat history and memory or not?
# - How to suppress the problem with % sign messing up output?
# - Show full exchange or only the answer?
# - Error handling 
# - Documentation
# - What's the best way to add this to magics?
# - Long term: Using the more advanced features of LangGraph, Agents, Multi-agentic workflows, etc. 


import argparse
from typing import Dict, Type

from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

from .base import BaseChatHandler, SlashCommandRoutingType

# LangGraph imports for using tools
import os
import re
import numpy as np
import math
from typing import Literal

from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState

# Chat Providers (add more as needed)
from langchain_aws import ChatBedrock
from langchain_ollama import ChatOllama
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_cohere import ChatCohere
from langchain_google_genai import ChatGoogleGenerativeAI


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

    # def __init__(self, retriever, *args, **kwargs):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self._retriever = retriever
        self.parser.prog = "/tools"
        self.parser.add_argument("query", nargs=argparse.REMAINDER)
        self.tools_file_path = os.path.join(self.output_dir, 'mytools.py') # Maybe pass as parameter?
        self.chat_provider = "" # Default, updated with function `setChatProvider`


    # https://python.langchain.com/v0.2/docs/integrations/platforms/
    def setChatProvider(self, provider): # For selecting the model to bind tools with
        try:
            if "bedrock" in provider.name.lower():
                chat_provider = "ChatBedrock"
            elif "ollama" in provider.name.lower():
                chat_provider = "ChatOllama"
            elif "anthropic" in provider.name.lower():
                chat_provider = "ChatAnthropic"
            elif "azure" in provider.name.lower():
                chat_provider = "AzureChatOpenAI"
            elif "openai" in provider.name.lower():
                chat_provider = "ChatOpenAI"
            elif "cohere" in provider.name.lower():
                chat_provider = "ChatCohere"
            elif "google" in provider.name.lower():
                chat_provider = "ChatGoogleGenerativeAI"
            return chat_provider
        except Exception as e:
            self.log.error(e)
            response = """The related chat provider is not supported."""
            self.reply(response)


    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        unified_parameters = {
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        llm = provider(**unified_parameters)
        self.chat_provider = self.setChatProvider(provider)
        self.llm = llm
        memory = ConversationBufferWindowMemory(
            memory_key="chat_history", return_messages=True, k=2
        )
        self.llm_chain = LLMChain(llm=self.llm, 
                                  prompt=CONDENSE_PROMPT, 
                                  memory=memory,
                                  verbose=False)


    # #### TOOLS FOR USE WITH LANGGRAPH #####
    """
    Bind tools to LLM and provide chat functionality. 
    Call:
        /tools <query>
    """

    def conditional_continue(state: MessagesState) -> Literal["tools", "__end__"]:
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return "__end__"

    def get_tool_names(tools_file_path):
        """
        Read a file and extract the function names following the @tool decorator.
        Args:
            file_path (str): The path to the file.
        Returns:
            list: A list of function names.
        """
        with open(tools_file_path, 'r') as file:
            content = file.read()
            # Use a regular expression to find the function names
            tool_pattern = r'@tool\n\s*def\s+(\w+)'
            tools = re.findall(tool_pattern, content)
        return tools

    def toolChat(self, query):
        print("TOOL CHAT", query)
        for chunk in self.app.stream({"messages": [("human", query)]}, stream_mode="values"):
            response = chunk["messages"][-1].pretty_print()
        return response

    
    ##### MAIN FUNCTION #####
    def useLLMwithTools(self, chat_provider, model_name, tools_file_path, query): 

        def call_tool(state: MessagesState):
            messages = state["messages"]
            response = self.model_with_tools.invoke(messages)
            return {"messages": [response]}

        # Read in the tools file
        file_path = tools_file_path
        with open(file_path) as file:
            exec(file.read())
        
        # Get tool names and create node with tools
        tools = ToolsChatHandler.get_tool_names(file_path)
        tools = [eval(j) for j in tools]
        tool_node = ToolNode(tools)
        
        # Bind tools to LLM
        if chat_provider=="ChatBedrock":
            self.model_with_tools = eval(chat_provider)(model_id=model_name, 
                                                model_kwargs={"temperature": 0}).bind_tools(tools)    
        else:
            self.model_with_tools = eval(chat_provider)(model=model_name, temperature=0).bind_tools(tools)

        # Initialize graph
        agentic_workflow = StateGraph(MessagesState)
        # Define the agent and tool nodes we will cycle between
        agentic_workflow.add_node("agent", call_tool)
        agentic_workflow.add_node("tools", tool_node)
        # Add edges to the graph
        agentic_workflow.add_edge("__start__", "agent")
        agentic_workflow.add_conditional_edges("agent", ToolsChatHandler.conditional_continue)
        agentic_workflow.add_edge("tools", "agent")
        # Compile graph
        app = agentic_workflow.compile()
        
        # Run query
        # res = ToolsChatHandler.toolChat(self, query)
        res = app.invoke({"messages": query})
        return res["messages"][-1].content


    async def process_message(self, message: HumanChatMessage):
        args = self.parse_args(message)
        if args is None:
            return
        query = " ".join(args.query)
        if not query:
            self.reply(f"{self.parser.format_usage()}", message)
            return

        self.get_llm_chain()
                
        try:
            with self.pending("Using LLM with tools ..."):
                # result = await self.llm_chain.acall({"question": query})
                response = self.useLLMwithTools(self.chat_provider, 
                                                self.llm.model_id, 
                                                self.tools_file_path, 
                                                query)
                self.reply(response, message)
        except Exception as e:
            self.log.error(e)
            response = """Sorry, tool usage failed. 
            Either (i) this LLM does not accept tools, (ii) there an error in 
            the custom tools file, (iii) you may also want to check the 
            location of the tools file, or (iv) you may need to install the 
            `langchain_<provider_name>` package. (v) Finally, check that you have 
            authorized access to the LLM."""
            self.reply(response, message)

