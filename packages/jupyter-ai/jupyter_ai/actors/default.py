from jupyter_ai_magics.utils import decompose_model_id
import ray
from ray.util.queue import Queue

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
    def __init__(self, reply_queue: Queue, log: Logger):
        super().__init__(reply_queue=reply_queue, log=log)
        self.provider = None
        self.chat_provider = None

    def create_chat_provider(self, provider: BaseProvider):
        memory = RemoteMemory(actor_name=ACTOR_TYPE.MEMORY)
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])
        self.provider = provider
        self.chat_provider = ConversationChain(
            llm=provider,
            prompt=prompt_template,
            verbose=True,
            memory=memory
        )

    def _get_chat_provider(self):
        actor = ray.get_actor(ACTOR_TYPE.CHAT_PROVIDER)
        o = actor.get_provider.remote()
        provider = ray.get(o)
        
        if not provider:
            return None
        
        if provider.__class__.__name__ != self.provider.__class__.__name__:
            self.create_chat_provider(provider)
        return self.chat_provider

    def _process_message(self, message: HumanChatMessage):
        chat_provider = self._get_chat_provider()
        if not chat_provider:
            response = "It seems like there is no chat provider set up currently to allow chat to work. Please follow the settings panel to configure a chat provider, before using the chat."
        else:
            response = self.chat_provider.predict(input=message.body)
        self.reply(response, message)
