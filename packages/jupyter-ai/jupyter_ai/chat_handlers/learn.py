import argparse
import json
import os
from typing import Any, Awaitable, Coroutine, List, Optional, Tuple

from dask.distributed import Client as DaskClient
from jupyter_ai.config_manager import ConfigManager
from jupyter_ai.document_loaders.directory import get_embeddings, split
from jupyter_ai.document_loaders.splitter import ExtensionSplitter, NotebookSplitter
from jupyter_ai.models import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    HumanChatMessage,
    IndexedDir,
    IndexMetadata,
)
from jupyter_core.paths import jupyter_data_dir
from langchain.schema import BaseRetriever, Document
from langchain.text_splitter import (
    LatexTextSplitter,
    MarkdownTextSplitter,
    PythonCodeTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain.vectorstores import FAISS

from .base import BaseChatHandler

INDEX_SAVE_DIR = os.path.join(jupyter_data_dir(), "jupyter_ai", "indices")
METADATA_SAVE_PATH = os.path.join(INDEX_SAVE_DIR, "metadata.json")


class LearnChatHandler(BaseChatHandler):
    def __init__(
        self, root_dir: str, dask_client_future: Awaitable[DaskClient], *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.root_dir = root_dir
        self.dask_client_future = dask_client_future
        self.parser.prog = "/learn"
        self.parser.add_argument("-v", "--verbose", action="store_true")
        self.parser.add_argument("-d", "--delete", action="store_true")
        self.parser.add_argument("-l", "--list", action="store_true")
        self.parser.add_argument(
            "-c", "--chunk-size", action="store", default=DEFAULT_CHUNK_SIZE, type=int
        )
        self.parser.add_argument(
            "-o",
            "--chunk-overlap",
            action="store",
            default=DEFAULT_CHUNK_OVERLAP,
            type=int,
        )
        self.parser.add_argument("path", nargs=argparse.REMAINDER)
        self.index_name = "default"
        self.index = None
        self.metadata = IndexMetadata(dirs=[])
        self.prev_em_id = None

        if not os.path.exists(INDEX_SAVE_DIR):
            os.makedirs(INDEX_SAVE_DIR)

        self._load()

    def _load(self):
        """Loads the vector store."""
        embeddings = self.get_embedding_model()
        if not embeddings:
            return
        if self.index is None:
            try:
                self.index = FAISS.load_local(
                    INDEX_SAVE_DIR, embeddings, index_name=self.index_name
                )
                self.load_metadata()
            except Exception as e:
                self.log.error("Could not load vector index from disk.")

    async def _process_message(self, message: HumanChatMessage):
        # If no embedding provider has been selected
        em_provider_cls, em_provider_args = self.get_embedding_provider()
        if not em_provider_cls:
            self.reply(
                "Sorry, please select an embedding provider before using the `/learn` command."
            )
            return

        args = self.parse_args(message)
        if args is None:
            return

        if args.delete:
            self.delete()
            self.reply(f"👍 I have deleted everything I previously learned.", message)
            return

        if args.list:
            self.reply(self._build_list_response())
            return

        # Make sure the path exists.
        if not len(args.path) == 1:
            self.reply(f"{self.parser.format_usage()}", message)
            return
        short_path = args.path[0]
        load_path = os.path.join(self.root_dir, short_path)
        if not os.path.exists(load_path):
            response = f"Sorry, that path doesn't exist: {load_path}"
            self.reply(response, message)
            return

        # delete and relearn index if embedding model was changed
        await self.delete_and_relearn()

        if args.verbose:
            self.reply(f"Loading and splitting files for {load_path}", message)

        await self.learn_dir(load_path, args.chunk_size, args.chunk_overlap)
        self.save()

        response = f"""🎉 I have learned documents at **{load_path}** and I am ready to answer questions about them.
        You can ask questions about these docs by prefixing your message with **/ask**."""
        self.reply(response, message)

    def _build_list_response(self):
        if not self.metadata.dirs:
            return "There are no docs that have been learned yet."

        dirs = [dir.path for dir in self.metadata.dirs]
        dir_list = "\n- " + "\n- ".join(dirs) + "\n\n"
        message = f"""I can answer questions from docs in these directories:
        {dir_list}"""
        return message

    async def learn_dir(self, path: str, chunk_size: int, chunk_overlap: int):
        dask_client = await self.dask_client_future
        splitter_kwargs = {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}
        splitters = {
            ".py": PythonCodeTextSplitter(**splitter_kwargs),
            ".md": MarkdownTextSplitter(**splitter_kwargs),
            ".tex": LatexTextSplitter(**splitter_kwargs),
            ".ipynb": NotebookSplitter(**splitter_kwargs),
        }
        splitter = ExtensionSplitter(
            splitters=splitters,
            default_splitter=RecursiveCharacterTextSplitter(**splitter_kwargs),
        )

        delayed = split(path, splitter=splitter)
        doc_chunks = await dask_client.compute(delayed)

        em_provider_cls, em_provider_args = self.get_embedding_provider()
        delayed = get_embeddings(doc_chunks, em_provider_cls, em_provider_args)
        embedding_records = await dask_client.compute(delayed)
        if self.index:
            self.index.add_embeddings(*embedding_records)
        else:
            self.create(*embedding_records)

        self._add_dir_to_metadata(path, chunk_size, chunk_overlap)
        self.prev_em_id = em_provider_cls.id + ":" + em_provider_args["model_id"]

    def _add_dir_to_metadata(self, path: str, chunk_size: int, chunk_overlap: int):
        dirs = self.metadata.dirs
        index = next((i for i, dir in enumerate(dirs) if dir.path == path), None)
        if not index:
            dirs.append(
                IndexedDir(
                    path=path, chunk_size=chunk_size, chunk_overlap=chunk_overlap
                )
            )
        self.metadata.dirs = dirs

    async def delete_and_relearn(self):
        """Delete the vector store and relearn all indexed directories if
        necessary. If the embedding model is unchanged, this method does
        nothing."""
        if not self.metadata.dirs:
            self.delete()
            return

        em_provider_cls, em_provider_args = self.get_embedding_provider()
        curr_em_id = em_provider_cls.id + ":" + em_provider_args["model_id"]
        prev_em_id = self.prev_em_id

        # TODO: Fix this condition to read the previous EM id from some
        # persistent source. Right now, we just skip this validation on server
        # init, meaning a user could switch embedding models in the config file
        # directly and break their instance.
        if (prev_em_id is None) or (prev_em_id == curr_em_id):
            return

        self.log.info(
            f"Switching embedding provider from {prev_em_id} to {curr_em_id}."
        )
        message = f"""🔔 Hi there, it seems like you have updated the embeddings
        model from `{prev_em_id}` to `{curr_em_id}`. I have to re-learn the
        documents you had previously submitted for learning. Please wait to use
        the **/ask** command until I am done with this task."""

        self.reply(message)

        metadata = self.metadata
        self.delete()
        await self.relearn(metadata)
        self.prev_em_id = curr_em_id

    def delete(self):
        self.index = None
        self.metadata = IndexMetadata(dirs=[])
        paths = [
            os.path.join(INDEX_SAVE_DIR, self.index_name + ext)
            for ext in [".pkl", ".faiss"]
        ]
        for path in paths:
            if os.path.isfile(path):
                os.remove(path)

    async def relearn(self, metadata: IndexMetadata):
        # Index all dirs in the metadata
        if not metadata.dirs:
            return

        for dir in metadata.dirs:
            # TODO: do not relearn directories in serial, but instead
            # concurrently or in parallel
            await self.learn_dir(dir.path, dir.chunk_size, dir.chunk_overlap)

        self.save()

        dir_list = (
            "\n- " + "\n- ".join([dir.path for dir in self.metadata.dirs]) + "\n\n"
        )
        message = f"""🎉 I am done learning docs in these directories:
        {dir_list} I am ready to answer questions about them.
        You can ask questions about these docs by prefixing your message with **/ask**."""
        self.reply(message)

    def create(
        self,
        embedding_records: List[Tuple[str, List[float]]],
        metadatas: Optional[List[dict]] = None,
    ):
        embeddings = self.get_embedding_model()
        if not embeddings:
            return
        self.index = FAISS.from_embeddings(
            text_embeddings=embedding_records, embedding=embeddings, metadatas=metadatas
        )
        self.save()

    def save(self):
        if self.index is not None:
            self.index.save_local(INDEX_SAVE_DIR, index_name=self.index_name)

        self.save_metadata()

    def save_metadata(self):
        with open(METADATA_SAVE_PATH, "w") as f:
            f.write(self.metadata.json())

    def load_metadata(self):
        if not os.path.exists(METADATA_SAVE_PATH):
            return

        with open(METADATA_SAVE_PATH, encoding="utf-8") as f:
            j = json.loads(f.read())
            self.metadata = IndexMetadata(**j)

    async def aget_relevant_documents(
        self, query: str
    ) -> Coroutine[Any, Any, List[Document]]:
        if not self.index:
            return []

        await self.delete_and_relearn()
        docs = self.index.similarity_search(query)
        return docs

    def get_embedding_provider(self):
        return self.config_manager.em_provider, self.config_manager.em_provider_params

    def get_embedding_model(self):
        em_provider_cls, em_provider_args = self.get_embedding_provider()
        if em_provider_cls is None:
            return None

        return em_provider_cls(**em_provider_args)


class Retriever(BaseRetriever):
    learn_chat_handler: LearnChatHandler = None

    def _get_relevant_documents(self, query: str) -> List[Document]:
        raise NotImplementedError()

    async def _aget_relevant_documents(
        self, query: str
    ) -> Coroutine[Any, Any, List[Document]]:
        docs = await self.learn_chat_handler.aget_relevant_documents(query)
        return docs
