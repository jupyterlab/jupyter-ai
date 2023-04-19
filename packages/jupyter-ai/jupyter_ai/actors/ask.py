from langchain import OpenAI
import ray
import time
from uuid import uuid4
from ray.util.queue import Queue
from langchain.chains import ConversationalRetrievalChain
from jupyter_ai.models import AgentChatMessage, HumanChatMessage
from jupyter_ai.actors.base import ACTOR_TYPE, BaseActor, Logger


@ray.remote
class AskActor(BaseActor):
    """Processes messages prefixed with /ask. This actor will
    send the message as input to a RetrieverQA chain, that
    follows the Retrieval and Generation (RAG) tehnique to
    query the documents from the index, and sends this context
    to the LLM to generate the final reply.
    """

    def __init__(self, reply_queue: Queue, log: Logger):
        super().__init__(log=log, reply_queue=reply_queue)
        index_actor = ray.get_actor(ACTOR_TYPE.LEARN.value)
        handle = index_actor.get_index.remote()
        vectorstore = ray.get(handle)
        if not vectorstore:
            return

        self.chat_history = []
        self.chat_provider = ConversationalRetrievalChain.from_llm(
            OpenAI(temperature=0, verbose=True),
            vectorstore.as_retriever()
        )

    def process_message(self, message: HumanChatMessage):
        query = message.body.split(' ', 1)[-1]
        
        index_actor = ray.get_actor(ACTOR_TYPE.LEARN.value)
        handle = index_actor.get_index.remote()
        vectorstore = ray.get(handle)
        # Have to reference the latest index
        self.chat_provider.retriever = vectorstore.as_retriever()
        
        result = self.chat_provider({"question": query, "chat_history": self.chat_history})
        reply = result['answer']
        self.chat_history.append((query, reply)) 
        agent_message = AgentChatMessage(
            id=uuid4().hex,
            time=time.time(),
            body=reply,
            reply_to=message.id
        )
        self.reply_queue.put(agent_message)