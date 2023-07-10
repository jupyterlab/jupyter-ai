import argparse
from typing import Dict, Type

from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.chains import ConversationalRetrievalChain

from .base import BaseChatHandler


class AskChatHandler(BaseChatHandler):
    """Processes messages prefixed with /ask. This actor will
    send the message as input to a RetrieverQA chain, that
    follows the Retrieval and Generation (RAG) tehnique to
    query the documents from the index, and sends this context
    to the LLM to generate the final reply.
    """

    def __init__(self, retriever, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._retriever = retriever
        self.parser.prog = "/ask"
        self.parser.add_argument("query", nargs=argparse.REMAINDER)

    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        self.llm = provider(**provider_params)
        self.chat_history = []
        self.llm_chain = ConversationalRetrievalChain.from_llm(
            self.llm, self._retriever
        )

    async def _process_message(self, message: HumanChatMessage):
        args = self.parse_args(message)
        if args is None:
            return
        query = " ".join(args.query)
        if not query:
            self.reply(f"{self.parser.format_usage()}", message)
            return

        self.get_llm_chain()

        try:
            # limit chat history to last 2 exchanges
            self.chat_history = self.chat_history[-2:]

            result = await self.llm_chain.acall(
                {"question": query, "chat_history": self.chat_history}
            )
            response = result["answer"]
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
