from typing import Dict, List, Type

from jupyter_ai.models import ChatMessage, ClearMessage, HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)

from .base import BaseChatHandler

SYSTEM_PROMPT = """
You are Jupyternaut, a conversational assistant living in JupyterLab to help users.
You are not a language model, but rather an application built on a foundation model from {provider_name} called {local_model_id}.
You are talkative and you provide lots of specific details from the foundation model's context.
You may use Markdown to format your response.
Code blocks must be formatted in Markdown.
Math should be rendered with inline TeX markup, surrounded by $.
If you do not know the answer to a question, answer truthfully by responding that you do not know.
The following is a friendly conversation between you and a human.
""".strip()

DEFAULT_TEMPLATE = """Current conversation:
{history}
Human: {input}
AI:"""


class DefaultChatHandler(BaseChatHandler):
    def __init__(self, chat_history: List[ChatMessage], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory = ConversationBufferWindowMemory(return_messages=True, k=2)
        self.chat_history = chat_history

    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        llm = provider(**provider_params)

        if llm.is_chat_provider:
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT).format(
                        provider_name=llm.name, local_model_id=llm.model_id
                    ),
                    MessagesPlaceholder(variable_name="history"),
                    HumanMessagePromptTemplate.from_template("{input}"),
                ]
            )
            self.memory = ConversationBufferWindowMemory(return_messages=True, k=2)
        else:
            prompt_template = PromptTemplate(
                input_variables=["history", "input"],
                template=SYSTEM_PROMPT.format(
                    provider_name=llm.name, local_model_id=llm.model_id
                )
                + "\n\n"
                + DEFAULT_TEMPLATE,
            )
            self.memory = ConversationBufferWindowMemory(k=2)

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
        if self.chat_history:
            self.chat_history.clear()

    async def _process_message(self, message: HumanChatMessage):
        self.get_llm_chain()
        response = await self.llm_chain.apredict(input=message.body, stop=["\nHuman:"])
        self.reply(response, message)
