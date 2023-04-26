import argparse
from jupyter_ai_magics.providers import BaseProvider

import ray
from ray.util.queue import Queue

from langchain import OpenAI
from langchain.chains import ConversationalRetrievalChain

from jupyter_ai.models import HumanChatMessage
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
        super().__init__(reply_queue=reply_queue, log=log)
        
        self.provider = None
        self.chat_provider = None
        self.parser.prog = '/ask'
        self.parser.add_argument('query', nargs=argparse.REMAINDER)

    def create_chat_provider(self, provider: BaseProvider):
        index_actor = ray.get_actor(ACTOR_TYPE.LEARN.value)
        handle = index_actor.get_index.remote()
        vectorstore = ray.get(handle)
        if not vectorstore:
            return None
        self.provider = provider
        self.chat_history = []
        self.chat_provider = ConversationalRetrievalChain.from_llm(
            provider,
            vectorstore.as_retriever()
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
        args = self.parse_args(message)
        if args is None:
            return
        query = ' '.join(args.query)
        if not query:
            self.reply(f"{self.parser.format_usage()}", message)
            return
        
        index_actor = ray.get_actor(ACTOR_TYPE.LEARN.value)
        handle = index_actor.get_index.remote()
        vectorstore = ray.get(handle)

        self._get_chat_provider()
        
        # Have to reference the latest index
        self.chat_provider.retriever = vectorstore.as_retriever()
        
        result = self.chat_provider({"question": query, "chat_history": self.chat_history})
        response = result['answer']
        self.chat_history.append((query, response))
        self.reply(response, message)
