from typing import Dict, Type
from uuid import uuid4
import time

from jupyter_ai.models import HumanChatMessage, AgentStreamMessage, AgentStreamChunkMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.chains import ConversationChain, LLMChain
from langchain.memory import ConversationBufferWindowMemory

from .base import BaseChatHandler, SlashCommandRoutingType
from ..history import BoundedChatHistory
from langchain_core.runnables.history import RunnableWithMessageHistory


class DefaultChatHandler(BaseChatHandler):
    id = "default"
    name = "Default"
    help = "Responds to prompts that are not otherwise handled by a chat handler"
    routing_type = SlashCommandRoutingType(slash_id=None)

    uses_llm = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        unified_parameters = {
            "verbose": True,
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        llm = provider(**unified_parameters)

        prompt_template = llm.get_chat_prompt_template()
        self.llm = llm
        self.memory = ConversationBufferWindowMemory(
            return_messages=llm.is_chat_provider, k=2
        )

        runnable = prompt_template | llm
        if not llm.manages_history:
            history = BoundedChatHistory(k=2)
            runnable = RunnableWithMessageHistory(
                runnable=runnable,
                get_session_history=lambda *args: history,
                input_messages_key="input",
                history_messages_key="history",
            )
        
        self.llm_chain = runnable


    def _start_stream(self, human_msg: HumanChatMessage) -> str:
        """
        Sends an `agent-stream` message to indicate the start of a response
        stream. Returns the ID of the message, denoted as the `stream_id`.
        """
        stream_id = uuid4().hex
        stream_msg = AgentStreamMessage(
            id=stream_id,
            time=time.time(),
            body="",
            reply_to=human_msg.id,
            persona=self.persona,
        )

        for handler in self._root_chat_handlers.values():
            if not handler:
                continue

            handler.broadcast_message(stream_msg)
            break

        return stream_id
    
    def _send_stream_chunk(self, stream_id: str, content: str, complete: bool = False):
        """
        Sends an `agent-stream-chunk` message containing content that should be
        appended to an existing `agent-stream` message with ID `stream_id`.
        """
        stream_chunk_msg = AgentStreamChunkMessage(
            id=stream_id,
            content=content,
            stream_complete=complete
        )

        for handler in self._root_chat_handlers.values():
            if not handler:
                continue

            handler.broadcast_message(stream_chunk_msg)
            break
    

    async def process_message(self, message: HumanChatMessage):
        self.get_llm_chain()

        stream_id = self._start_stream(human_msg=message)
        async for chunk in self.llm_chain.astream({ "input": message.body }, config={"configurable": {"session_id": "static_session"}}):
            self.log.error(chunk.content)
            self._send_stream_chunk(stream_id, chunk.content)
        
        self._send_stream_chunk(stream_id, "", complete=True)

        # with self.pending("Generating response"):
        #     response = await self.llm_chain.apredict(
        #         input=message.body, stop=["\nHuman:"]
        #     )
        # self.reply(response, message)
