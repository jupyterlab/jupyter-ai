# This file is for illustrative purposes
# It is to be deleted before merging
from jupyter_ai.models import HumanChatMessage
from langchain_community.retrievers import WikipediaRetriever
from langchain_community.retrievers import ArxivRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .base import BaseContextProvider, BaseCommandContextProvider


# Examples of the ease of implementing retriever based context providers
ARXIV_TEMPLATE = """
Title: {title}
Publish Date: {publish_date}
'''
{content}
'''
""".strip()


class ArxivContextProvider(BaseCommandContextProvider):
    id = "arvix"
    description = "Include papers from Arxiv"
    remove_from_prompt = True
    header = "Following are snippets of research papers:"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.retriever = ArxivRetriever()

    async def make_context_prompt(self, message: HumanChatMessage) -> str:
        if not self._find_instances(message.prompt):
            return ""
        query = self._clean_prompt(message.body)
        docs = await self.retriever.ainvoke(query)
        context = "\n\n".join(
            [
                ARXIV_TEMPLATE.format(
                    content=d.page_content,
                    title=d.metadata["Title"],
                    publish_date=d.metadata["Published"],
                )
                for d in docs
            ]
        )
        return self.header + "\n" + context


# Another retriever based context provider with a rewrite step using LLM
WIKI_TEMPLATE = """
Title: {title}
'''
{content}
'''
""".strip()

REWRITE_TEMPLATE = """Provide a better search query for \
web search engine to answer the given question, end \
the queries with ’**’. Question: \
{x} Answer:"""


class WikiContextProvider(BaseCommandContextProvider):
    id = "wiki"
    description = "Include knowledge from Wikipedia"
    remove_from_prompt = True
    header = "Following are information from wikipedia:"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.retriever = WikipediaRetriever()

    async def make_context_prompt(self, message: HumanChatMessage) -> str:
        if not self._find_instances(message.prompt):
            return ""
        prompt = self._clean_prompt(message.body)
        search_query = await self._rewrite_prompt(prompt)
        docs = await self.retriever.ainvoke(search_query)
        context = "\n\n".join(
            [
                WIKI_TEMPLATE.format(
                    content=d.page_content,
                    title=d.metadata["title"],
                )
                for d in docs
            ]
        )
        return self.header + "\n" + context

    async def _rewrite_prompt(self, prompt: str) -> str:
        return await self.get_llm_chain().ainvoke(prompt)

    def get_llm_chain(self):
        # from https://github.com/langchain-ai/langchain/blob/master/cookbook/rewrite.ipynb
        llm = self.get_llm()
        rewrite_prompt = ChatPromptTemplate.from_template(REWRITE_TEMPLATE)

        def _parse(text):
            return text.strip('"').strip("**")

        return rewrite_prompt | llm | StrOutputParser() | _parse


# Partial example of non-command context provider for errors.
# Assuming there is an option in UI to add cell errors to messages,
# default chat will automatically invoke this context provider to add
# solutions retrieved from a custom error database or a stackoverflow / google
# retriever pipeline to find solutions for errors.
class ErrorContextProvider(BaseContextProvider):
    id = "error"
    description = "Include custom error context"
    remove_from_prompt = True
    header = "Following are potential solutions for the error:"
    is_command = False  # will not show up in autocomplete

    async def make_context_prompt(self, message: HumanChatMessage) -> str:
        # will run for every message with a cell error since it does not
        # use _find_instances to  check for the presence of the command in
        # the message.
        if not (message.selection and message.selection.type == "cell-with-error"):
            return ""
        docs = await self.solution_retriever.ainvoke(message.selection)
        if not docs:
            return ""
        context = "\n\n".join([d.page_content for d in docs])
        return self.header + "\n" + context

    @property
    def solution_retriever(self):
        # retriever that takes an error and returns a solutions from a database
        # of error messages.
        raise NotImplementedError("Error retriever not implemented")
