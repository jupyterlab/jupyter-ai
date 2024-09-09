import time
from typing import Dict, Type
from uuid import uuid4

from jupyter_ai.models import (
    AgentStreamChunkMessage,
    AgentStreamMessage,
    HumanChatMessage,
)
from jupyter_ai_magics.providers import BaseProvider
from langchain_core.messages import AIMessageChunk
from langchain_core.runnables import ConfigurableFieldSpec
from langchain_core.runnables.history import RunnableWithMessageHistory

from ..models import HumanChatMessage
from .base import BaseChatHandler, SlashCommandRoutingType


class DefaultChatHandler(BaseChatHandler):
    id = "default"
    name = "Default"
    help = "Responds to prompts that are not otherwise handled by a chat handler"
    routing_type = SlashCommandRoutingType(slash_id=None)

    uses_llm = True
    supports_help = False

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

        runnable = prompt_template | llm
        if not llm.manages_history:
            runnable = RunnableWithMessageHistory(
                runnable=runnable,
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
            complete=False,
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
            id=stream_id, content=content, stream_complete=complete
        )

        for handler in self._root_chat_handlers.values():
            if not handler:
                continue

            handler.broadcast_message(stream_chunk_msg)
            break

    async def process_message(self, message: HumanChatMessage):
        self.get_llm_chain()
        received_first_chunk = False

        # start with a pending message
        with self.pending("Generating response", message) as pending_message:
            # stream response in chunks. this works even if a provider does not
            # implement streaming, as `astream()` defaults to yielding `_call()`
            # when `_stream()` is not implemented on the LLM class.
            async for chunk in self.llm_chain.astream(
                {"input": message.body},
                config={"configurable": {"last_human_msg": message}},
            ):
                if not received_first_chunk:
                    # when receiving the first chunk, close the pending message and
                    # start the stream.
                    self.close_pending(pending_message)
                    stream_id = self._start_stream(human_msg=message)
                    received_first_chunk = True

                if isinstance(chunk, AIMessageChunk):
                    self._send_stream_chunk(stream_id, chunk.content)
                elif isinstance(chunk, str):
                    self._send_stream_chunk(stream_id, chunk)
                else:
                    self.log.error(f"Unrecognized type of chunk yielded: {type(chunk)}")
                    break

            # complete stream after all chunks have been streamed
            self._send_stream_chunk(stream_id, "", complete=True)
