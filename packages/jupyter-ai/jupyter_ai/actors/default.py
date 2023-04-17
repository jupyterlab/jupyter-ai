import time
from uuid import uuid4
from jupyter_ai.actors.base import BaseActor, Logger, ACTOR_TYPE
from jupyter_ai.actors.memory import RemoteMemory
from jupyter_ai.models import AgentChatMessage, HumanChatMessage
from jupyter_ai_magics.providers import ChatOpenAINewProvider
from langchain import ConversationChain
import ray
from ray.util.queue import Queue
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate, 
    MessagesPlaceholder, 
    SystemMessagePromptTemplate, 
    HumanMessagePromptTemplate
)

# [W 2023-04-17 08:54:34.187 ServerApp] 404 GET /api/ai/chats?token=[secret]
# (e9e4e29d33d44ab4a7c2838cbce85646@127.0.0.1) 21.38ms referer=None


@ray.remote
class DefaultActor(BaseActor):
    def __init__(self, reply_queue: Queue, log: Logger):
        super().__init__(log=log, reply_queue=reply_queue)
        # TODO: Should take the provider/model id as strings
        provider = ChatOpenAINewProvider(model_id="gpt-3.5-turbo")
        
        # Create a conversation memory
        memory = RemoteMemory(actor_name=ACTOR_TYPE.MEMORY)
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template("The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know."),
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