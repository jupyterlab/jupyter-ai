from typing import Dict, List, Type

from jupyter_ai.models import ChatMessage, ClearMessage, HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.chains import ConversationChain, LLMChain
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
        unified_parameters = {
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        llm = provider(**unified_parameters)

        prompt_template = llm.get_chat_prompt_template()
        self.llm = llm
        self.memory = ConversationBufferWindowMemory(
            return_messages=llm.is_chat_provider, k=2
        )

        if llm.manages_history:
            self.llm_chain = LLMChain(llm=llm, prompt=prompt_template, verbose=True)

        else:
            self.llm_chain = ConversationChain(
                llm=llm, prompt=prompt_template, verbose=True, memory=self.memory
            )

    async def process_message(self, message: HumanChatMessage):
        self.get_llm_chain()
        with self.pending("Generating response"):
            response = await self.llm_chain.apredict(
                input=message.body, stop=["\nHuman:"]
            )
        self.reply(response, message)
