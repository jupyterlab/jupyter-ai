from typing import Dict, Type, List
import ray

from langchain import ConversationChain
from langchain.prompts import (
    ChatPromptTemplate, 
    MessagesPlaceholder, 
    SystemMessagePromptTemplate, 
    HumanMessagePromptTemplate
)

from jupyter_ai.actors.base import BaseActor, Logger, ACTOR_TYPE
from jupyter_ai.actors.memory import RemoteMemory
from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider

SYSTEM_PROMPT = "The following is a friendly conversation between a human and an AI, whose name is Jupyter AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know."

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
            SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}")
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
        response = self.llm_chain.predict(input=message.body)
        self.reply(response, message)
