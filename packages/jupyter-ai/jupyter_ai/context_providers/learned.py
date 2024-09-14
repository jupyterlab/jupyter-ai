from typing import List

from jupyter_ai.chat_handlers.learn import Retriever
from jupyter_ai.models import HumanChatMessage

from .base import BaseCommandContextProvider
from .file import FileContextProvider

FILE_CHUNK_TEMPLATE = """
Snippet from file: {filepath}
```
{content}
```
""".strip()


class LearnedContextProvider(BaseCommandContextProvider):
    id = "learned"
    description = "Include learned context"
    remove_from_prompt = True
    header = "Following are snippets from potentially relevant files:"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.retriever = Retriever(learn_chat_handler=self.chat_handlers["/learn"])

    async def make_context_prompt(self, message: HumanChatMessage) -> str:
        if not self.retriever or not self._find_commands(message.prompt):
            return ""
        query = self._clean_prompt(message.body)
        docs = await self.retriever.ainvoke(query)
        excluded = self._get_repeated_files(message)
        context = "\n\n".join(
            [
                FILE_CHUNK_TEMPLATE.format(
                    filepath=d.metadata["path"], content=d.page_content
                )
                for d in docs
                if d.metadata["path"] not in excluded and d.page_content
            ]
        )
        return self.header + "\n" + context

    def _get_repeated_files(self, message: HumanChatMessage) -> List[str]:
        # don't include files that are already provided by the file context provider
        file_context_provider = self.context_providers.get("file")
        if isinstance(file_context_provider, FileContextProvider):
            return file_context_provider.get_filepaths(message)
        return []
