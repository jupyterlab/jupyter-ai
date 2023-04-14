import os
import time
from uuid import uuid4
from jupyter_ai.models import AgentChatMessage, ChatMessage, HumanChatMessage
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


@ray.remote
class Router():
    def __init__(self, reply_queue: Queue):
        pass


@ray.remote
class FileSystemActor():
    def __init__(self, reply_queue: Queue):
        self.reply_queue = reply_queue

    def process_message(self, msg):
        reply = f"FileSystemActor: Processed message {msg}"
        self.reply_queue.put(reply)

@ray.remote
class DefaultActor():
    def __init__(self, reply_queue: Queue):
        # TODO: Should take the provider/model id as strings
        
        self.reply_queue = reply_queue
        if ChatOpenAINewProvider.auth_strategy.name in os.environ:
            provider = ChatOpenAINewProvider(model_id="gpt-3.5-turbo")
            
            # Create a conversation memory
            memory = ConversationBufferMemory(return_messages=True)
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
        if self.chat_provider:
            response = self.chat_provider.predict(input=message.body)
            agent_message = AgentChatMessage(
                id=uuid4().hex,
                time=time.time(),
                body=response,
                reply_to=message.id
            )
            self.reply_queue.put(agent_message)



