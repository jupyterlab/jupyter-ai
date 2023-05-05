from typing import Dict, Type, List
import ray

from langchain import ConversationChain
from langchain.prompts import (
    ChatPromptTemplate, 
    MessagesPlaceholder, 
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate
)
from langchain.schema import (
    AIMessage,
)

from jupyter_ai.actors.base import BaseActor, ACTOR_TYPE
from jupyter_ai.actors.memory import RemoteMemory
from jupyter_ai.models import HumanChatMessage, ClearMessage, ChatMessage
from jupyter_ai_magics.providers import BaseProvider

SYSTEM_PROMPT = """
You are Jupyternaut, a conversational assistant living in JupyterLab to help users.
You are not a language model, but rather an application built on a foundation model from {provider_name} called {local_model_id}.
You are talkative and provides lots of specific details from its context.
You may use Markdown to format your response.
Code blocks must be formatted in Markdown.
Math should be rendered with inline TeX markup, surrounded by $.
If you do not know the answer to a question, answer truthfully by responding that you do not know.
The following is a friendly conversation between you and a human.
""".strip()

@ray.remote
class DefaultActor(BaseActor):
    def __init__(self, chat_history: List[ChatMessage], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory = None
        self.chat_history = chat_history

    def create_llm_chain(self, provider: Type[BaseProvider], provider_params: Dict[str, str]):
        llm = provider(**provider_params)
        self.memory = RemoteMemory(actor_name=ACTOR_TYPE.MEMORY)
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT).format(provider_name=llm.name, local_model_id=llm.model_id),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}"),
            AIMessage(content="")
        ])
        self.llm = llm
        self.llm_chain = ConversationChain(
            llm=llm,
            prompt=prompt_template,
            verbose=True,
            memory=self.memory
        )
    
    def clear_memory(self):
        if not self.memory:
            return
        
        # clear chain memory
        self.memory.clear()

        # clear transcript for existing chat clients
        reply_message = ClearMessage()
        self.reply_queue.put(reply_message)

        # clear transcript for new chat clients
        self.chat_history.clear()

    def _process_message(self, message: HumanChatMessage):
        self.get_llm_chain()
        response = self.llm_chain.predict(
            input=message.body,
            stop=["\nHuman:"]
        )
        self.reply(response, message)
