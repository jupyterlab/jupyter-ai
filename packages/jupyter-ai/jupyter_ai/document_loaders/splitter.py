import copy
from typing import Optional

from langchain.schema import Document
from langchain.text_splitter import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
    TextSplitter,
)


class ExtensionSplitter(TextSplitter):
    def __init__(self, splitters, default_splitter=None):
        self.splitters = splitters
        if default_splitter is None:
            self.default_splitter = RecursiveCharacterTextSplitter()
        else:
            self.default_splitter = default_splitter

    def split_text(self, text: str, metadata=None):
        splitter = self.splitters.get(metadata["extension"], self.default_splitter)
        return splitter.split_text(text)

    def create_documents(
        self, texts: list[str], metadatas: Optional[list[dict]] = None
    ) -> list[Document]:
        _metadatas = metadatas or [{}] * len(texts)
        documents = []
        for i, text in enumerate(texts):
            metadata = copy.deepcopy(_metadatas[i])
            for chunk in self.split_text(text, metadata):
                new_doc = Document(page_content=chunk, metadata=metadata)
                documents.append(new_doc)
        return documents


import nbformat


class NotebookSplitter(TextSplitter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.markdown_splitter = MarkdownTextSplitter(
            chunk_size=self._chunk_size, chunk_overlap=self._chunk_overlap
        )

    def split_text(self, text: str):
        nb = nbformat.reads(text, as_version=4)
        md = "\n\n".join([cell.source for cell in nb.cells])
        return self.markdown_splitter.split_text(md)
