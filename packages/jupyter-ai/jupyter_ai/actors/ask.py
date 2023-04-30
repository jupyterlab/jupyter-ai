import argparse
from typing import Dict, List, Type
from jupyter_ai_magics.providers import BaseProvider

import ray
from ray.util.queue import Queue

from langchain.chains import ConversationalRetrievalChain
from langchain.schema import BaseRetriever, Document

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

    def create_llm_chain(self, provider: Type[BaseProvider], provider_params: Dict[str, str]):
        retriever = Retriever()
        self.llm = provider(**provider_params)
        self.chat_history = []
        self.llm_chain = ConversationalRetrievalChain.from_llm(
            self.llm,
            retriever
        )

    def _process_message(self, message: HumanChatMessage):
        args = self.parse_args(message)
        if args is None:
            return
        query = ' '.join(args.query)
        if not query:
            self.reply(f"{self.parser.format_usage()}", message)
            return
        
        self.get_llm_chain()

        try:
            result = self.llm_chain({"question": query, "chat_history": self.chat_history})
            response = result['answer']
            self.chat_history.append((query, response))
            self.reply(response, message)
        except AssertionError as e:
            self.log.error(e)
            response = """Sorry, an error occurred while reading the from the learned documents. 
            If you have changed the embedding provider, try deleting the existing index by running 
            `/learn -d` command and then re-submitting the `learn <directory>` to learn the documents,
            and then asking the question again.
            """
            self.reply(response, message)


class Retriever(BaseRetriever):
    """Wrapper retriever class to get relevant docs
    from the vector store, this is important because
    of inconsistent de-serialization of index when it's
    accessed directly from the ask actor.
    """
    
    def get_relevant_documents(self, question: str):
        index_actor = ray.get_actor(ACTOR_TYPE.LEARN.value)
        docs = ray.get(index_actor.get_relevant_documents.remote(question))
        return docs
    
    async def aget_relevant_documents(self, query: str) -> List[Document]:
        return await super().aget_relevant_documents(query)