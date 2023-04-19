import time
from uuid import uuid4


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
from jupyter_ai.models import AgentChatMessage, HumanChatMessage
from jupyter_ai_magics.providers import ChatOpenAINewProvider

SYSTEM_PROMPT = "The following is a friendly conversation between a human and an AI, whose name is Jupyter AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know."

@ray.remote
class DefaultActor(BaseActor):
    def __init__(self, reply_queue: Queue, log: Logger):
        super().__init__(log=log, reply_queue=reply_queue)
        # TODO: Should take the provider/model id as strings
        provider = ChatOpenAINewProvider(model_id="gpt-3.5-turbo")
        
        # Create a conversation memory
        memory = RemoteMemory(actor_name=ACTOR_TYPE.MEMORY)
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])
        chain = ConversationChain(
            llm=provider, 
            prompt=prompt_template,
            verbose=True,
            memory=memory
        )
        self.chat_provider = chain

    def process_message(self, message: HumanChatMessage):
        response = self.chat_provider.predict(input=message.body)
        agent_message = AgentChatMessage(
            id=uuid4().hex,
            time=time.time(),
            body=response,
            reply_to=message.id
        )
        self.reply_queue.put(agent_message)