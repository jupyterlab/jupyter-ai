import argparse
from typing import Dict, Type

from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate

from .base import BaseChatHandler, SlashCommandRoutingType

PROMPT_TEMPLATE = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""
CONDENSE_PROMPT = PromptTemplate.from_template(PROMPT_TEMPLATE)


class AskChatHandler(BaseChatHandler):
    """Processes messages prefixed with /ask. This actor will
    send the message as input to a RetrieverQA chain, that
    follows the Retrieval and Generation (RAG) technique to
    query the documents from the index, and sends this context
    to the LLM to generate the final reply.
    """

    id = "ask"
    name = "Ask with Local Data"
    help = "Ask a question about your learned data"
    routing_type = SlashCommandRoutingType(slash_id="ask")

    uses_llm = True

    def __init__(self, retriever, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._retriever = retriever
        self.parser.prog = "/ask"
        self.parser.add_argument("query", nargs=argparse.REMAINDER)

    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        unified_parameters = {
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        self.llm = provider(**unified_parameters)
        memory = ConversationBufferWindowMemory(
            memory_key="chat_history", return_messages=True, k=2
        )
        self.llm_chain = ConversationalRetrievalChain.from_llm(
            self.llm,
            self._retriever,
            memory=memory,
            condense_question_prompt=CONDENSE_PROMPT,
            verbose=False,
        )

    async def process_message(self, message: HumanChatMessage):
        args = self.parse_args(message)
        if args is None:
            return
        query = " ".join(args.query)
        if not query:
            self.reply(f"{self.parser.format_usage()}", message)
            return

        self.get_llm_chain()

        try:
            with self.pending("Searching learned documents", message):
                assert self.llm_chain
                result = await self.llm_chain.acall({"question": query})
                response = result["answer"]
            self.reply(response, message)
        except AssertionError as e:
            self.log.error(e)
            response = """Sorry, an error occurred while reading the from the learned documents.
            If you have changed the embedding provider, try deleting the existing index by running
            `/learn -d` command and then re-submitting the `learn <directory>` to learn the documents,
            and then asking the question again.
            """
            self.reply(response, message)
