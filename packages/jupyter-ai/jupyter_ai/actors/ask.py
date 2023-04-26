import argparse
from typing import Dict
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

        self.parser.prog = '/ask'
        self.parser.add_argument('query', nargs=argparse.REMAINDER)

    def create_llm_chain(self, provider: BaseProvider, provider_params: Dict[str, str]):
        index_actor = ray.get_actor(ACTOR_TYPE.LEARN.value)
        handle = index_actor.get_index.remote()
        vectorstore = ray.get(handle)
        if not vectorstore:
            return None
        self.llm = provider(**provider_params)
        self.chat_history = []
        self.llm_chain = ConversationalRetrievalChain.from_llm(
            self.llm,
            vectorstore.as_retriever()
        )

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

        self.get_llm_chain()
        
        # Have to reference the latest index
        self.llm_chain.retriever = vectorstore.as_retriever()
        
        result = self.llm_chain({"question": query, "chat_history": self.chat_history})
        response = result['answer']
        self.chat_history.append((query, response))
        self.reply(response, message)
