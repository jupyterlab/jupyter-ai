from typing import Dict, List, Type

from jupyter_ai.models import ChatMessage, ClearMessage, HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory

from .base import BaseChatHandler, SlashCommandRoutingType


class DefaultChatHandler(BaseChatHandler):
    id = "default"
    name = "Default"
    help = "Responds to prompts that are not otherwise handled by a chat handler"
    routing_type = SlashCommandRoutingType(slash_id=None)

    uses_llm = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory = ConversationBufferWindowMemory(return_messages=True, k=2)

    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        model_parameters = self.get_model_parameters(provider, provider_params)
        llm = provider(**provider_params, **model_parameters)

        prompt_template = llm.get_chat_prompt_template()
        self.memory = ConversationBufferWindowMemory(
            return_messages=llm.is_chat_provider, k=2
        )

        self.llm = llm
        self.llm_chain = ConversationChain(
            llm=llm, prompt=prompt_template, verbose=True, memory=self.memory
        )

    def clear_memory(self):
        # clear chain memory
        if self.memory:
            self.memory.clear()

        # clear transcript for existing chat clients
        reply_message = ClearMessage()
        self.reply(reply_message)

        # clear transcript for new chat clients
        if self._chat_history:
            self._chat_history.clear()

    async def process_message(self, message: HumanChatMessage):
        self.get_llm_chain()
        response = await self.llm_chain.apredict(input=message.body, stop=["\nHuman:"])
        self.reply(response, message)
