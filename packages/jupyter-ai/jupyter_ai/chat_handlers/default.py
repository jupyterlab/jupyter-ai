import asyncio
import time
from typing import Any, Dict, Optional, Type
from uuid import uuid4

from jupyter_ai.callback_handlers import MetadataCallbackHandler
from jupyter_ai.models import (
    AgentStreamChunkMessage,
    AgentStreamMessage,
    HumanChatMessage,
)
from jupyter_ai_magics.providers import BaseProvider
from langchain_core.messages import AIMessageChunk
from langchain_core.outputs.generation import GenerationChunk
from langchain_core.runnables import ConfigurableFieldSpec
from langchain_core.runnables.history import RunnableWithMessageHistory

try:
    from jupyterlab_collaborative_chat.ychat import YChat
except:
    from typing import Any as YChat

from ..context_providers import ContextProviderException, find_commands
from .base import BaseChatHandler, SlashCommandRoutingType


class GenerationInterrupted(asyncio.CancelledError):
    """Exception raised when streaming is cancelled by the user"""


class DefaultChatHandler(BaseChatHandler):
    id = "default"
    name = "Default"
    help = "Responds to prompts that are not otherwise handled by a chat handler"
    routing_type = SlashCommandRoutingType(slash_id=None)

    uses_llm = True
    supports_help = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt_template = None

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
        self.prompt_template = prompt_template

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

    def _start_stream(self, human_msg: HumanChatMessage, chat: Optional[YChat]) -> str:
        """
        Sends an `agent-stream` message to indicate the start of a response
        stream. Returns the ID of the message, denoted as the `stream_id`.
        """
        if chat is not None:
            stream_id = self.write_message(chat, "")
        else:
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

    def _send_stream_chunk(
        self,
        stream_id: str,
        content: str,
        chat: YChat | None,
        complete: bool = False,
        metadata: Dict[str, Any] = {},
    ):
        """
        Sends an `agent-stream-chunk` message containing content that should be
        appended to an existing `agent-stream` message with ID `stream_id`.
        """
        if chat is not None:
            self.write_message(chat, content, stream_id)
        else:
            stream_chunk_msg = AgentStreamChunkMessage(
                id=stream_id,
                content=content,
                stream_complete=complete,
                metadata=metadata,
            )
            for handler in self._root_chat_handlers.values():
                if not handler:
                    continue

                handler.broadcast_message(stream_chunk_msg)
                break

    async def process_message(self, message: HumanChatMessage, chat: Optional[YChat]):
        self.get_llm_chain()
        received_first_chunk = False
        assert self.llm_chain

        inputs = {"input": message.body}
        if "context" in self.prompt_template.input_variables:
            # include context from context providers.
            try:
                context_prompt = await self.make_context_prompt(message)
            except ContextProviderException as e:
                self.reply(str(e), message)
                return
            inputs["context"] = context_prompt
            inputs["input"] = self.replace_prompt(inputs["input"])

        # start with a pending message
        with self.pending("Generating response", message, chat=chat) as pending_message:
            # stream response in chunks. this works even if a provider does not
            # implement streaming, as `astream()` defaults to yielding `_call()`
            # when `_stream()` is not implemented on the LLM class.
            metadata_handler = MetadataCallbackHandler()
            chunk_generator = self.llm_chain.astream(
                inputs,
                config={
                    "configurable": {"last_human_msg": message},
                    "callbacks": [metadata_handler],
                },
            )
            stream_interrupted = False
            async for chunk in chunk_generator:
                if not received_first_chunk:
                    # when receiving the first chunk, close the pending message and
                    # start the stream.
                    self.close_pending(pending_message, chat=chat)
                    stream_id = self._start_stream(message, chat)
                    received_first_chunk = True
                    self.message_interrupted[stream_id] = asyncio.Event()

                if self.message_interrupted[stream_id].is_set():
                    try:
                        # notify the model provider that streaming was interrupted
                        # (this is essential to allow the model to stop generating)
                        await chunk_generator.athrow(GenerationInterrupted())
                    except GenerationInterrupted:
                        # do not let the exception bubble up in case if
                        # the provider did not handle it
                        pass
                    stream_interrupted = True
                    break

                if isinstance(chunk, AIMessageChunk) and isinstance(chunk.content, str):
                    self._send_stream_chunk(stream_id, chunk.content, chat)
                elif isinstance(chunk, str):
                    self._send_stream_chunk(stream_id, chunk, chat)
                else:
                    self.log.error(f"Unrecognized type of chunk yielded: {type(chunk)}")
                    break

            # complete stream after all chunks have been streamed
            stream_tombstone = (
                "\n\n(AI response stopped by user)" if stream_interrupted else ""
            )
            self._send_stream_chunk(
                stream_id,
                stream_tombstone,
                chat,
                complete=True,
                metadata=metadata_handler.jai_metadata,
            )
            del self.message_interrupted[stream_id]

    async def make_context_prompt(self, human_msg: HumanChatMessage) -> str:
        return "\n\n".join(
            await asyncio.gather(
                *[
                    provider.make_context_prompt(human_msg)
                    for provider in self.context_providers.values()
                    if find_commands(provider, human_msg.prompt)
                ]
            )
        )

    def replace_prompt(self, prompt: str) -> str:
        # modifies prompt by the context providers.
        # some providers may modify or remove their '@' commands from the prompt.
        for provider in self.context_providers.values():
            prompt = provider.replace_prompt(prompt)
        return prompt
