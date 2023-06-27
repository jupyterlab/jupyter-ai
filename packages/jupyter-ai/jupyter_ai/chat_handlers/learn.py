import argparse
import json
import os
import time
from typing import List, Coroutine, Any

from dask.distributed import Client as DaskClient

from jupyter_core.paths import jupyter_data_dir

from langchain import FAISS
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter, PythonCodeTextSplitter,
    MarkdownTextSplitter, LatexTextSplitter
)
from langchain.schema import Document

from .base import BaseChatHandler
from jupyter_ai.models import HumanChatMessage, IndexedDir, IndexMetadata
from jupyter_ai.document_loaders.directory import split, get_embeddings
from jupyter_ai.document_loaders.splitter import ExtensionSplitter, NotebookSplitter
from jupyter_ai.models import HumanChatMessage, IndexedDir, IndexMetadata
from jupyter_core.paths import jupyter_data_dir
from langchain import FAISS
from langchain.schema import BaseRetriever, Document
from langchain.text_splitter import (
    LatexTextSplitter,
    MarkdownTextSplitter,
    PythonCodeTextSplitter,
    RecursiveCharacterTextSplitter,
)

INDEX_SAVE_DIR = os.path.join(jupyter_data_dir(), "jupyter_ai", "indices")
METADATA_SAVE_PATH = os.path.join(INDEX_SAVE_DIR, "metadata.json")


def compute_delayed(delayed):
    return delayed.compute()

class LearnChatHandler(BaseChatHandler, BaseRetriever):
    def __init__(self, root_dir: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_dir = root_dir
        self.chunk_size = 2000
        self.chunk_overlap = 100
        self.parser.prog = "/learn"
        self.parser.add_argument("-v", "--verbose", action="store_true")
        self.parser.add_argument("-d", "--delete", action="store_true")
        self.parser.add_argument("-l", "--list", action="store_true")
        self.parser.add_argument("path", nargs=argparse.REMAINDER)
        self.index_name = "default"
        self.index = None
        self.metadata = IndexMetadata(dirs=[])
        self.prev_em_id = None
        self.embeddings = None
        
        # initialize dask client
        self.dask_client = DaskClient(processes=False)

        if not os.path.exists(INDEX_SAVE_DIR):
            os.makedirs(INDEX_SAVE_DIR)

        self.load_or_create()

    def _process_message(self, message: HumanChatMessage):
        if not self.index:
            self.load_or_create()

        # If index is not still there, embeddings are not present
        if not self.index:
            self.reply(
                "Sorry, please select an embedding provider before using the `/learn` command."
            )

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

        if args.verbose:
            self.reply(f"Loading and splitting files for {load_path}", message)

        self.learn_dir(load_path)
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

    def learn_dir(self, path: str):
        start = time.time()
        splitters={
            '.py': PythonCodeTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap),
            '.md': MarkdownTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap),
            '.tex': LatexTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap),
            '.ipynb': NotebookSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        }
        splitter = ExtensionSplitter(
            splitters=splitters,
            default_splitter=RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
            ),
        )

        delayed = split(path, splitter=splitter)
        future = self.dask_client.submit(compute_delayed, delayed)
        doc_chunks = future.result()

        self.log.error(f"[/learn] Finished chunking documents. Time: {round((time.time() - start) * 1000)}ms")

        em = self.get_embedding_model()
        delayed = get_embeddings(doc_chunks, em)
        future = self.dask_client.submit(compute_delayed, delayed)
        embedding_records = future.result()
        self.log.error(f"[/learn] Finished computing embeddings. Time: {round((time.time() - start) * 1000)}ms")

        self.index.add_embeddings(*embedding_records)
        self._add_dir_to_metadata(path)
        
        self.log.error(f"[/learn] Complete. Time: {round((time.time() - start) * 1000)}ms")
    
    def _add_dir_to_metadata(self, path: str):
        dirs = self.metadata.dirs
        index = next((i for i, dir in enumerate(dirs) if dir.path == path), None)
        if not index:
            dirs.append(IndexedDir(path=path))
        self.metadata.dirs = dirs

    def delete_and_relearn(self):
        if not self.metadata.dirs:
            self.delete()
            return
        message = """🔔 Hi there, It seems like you have updated the embeddings model. For the **/ask**
        command to work with the new model, I have to re-learn the documents you had previously
        submitted for learning. Please wait to use the **/ask** command until I am done with this task."""
        self.reply(message)

        metadata = self.metadata
        self.delete()
        self.relearn(metadata)

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
        self.create()

    def relearn(self, metadata: IndexMetadata):
        # Index all dirs in the metadata
        if not metadata.dirs:
            return

        for dir in metadata.dirs:
            self.learn_dir(dir.path)

        self.save()

        dir_list = (
            "\n- " + "\n- ".join([dir.path for dir in self.metadata.dirs]) + "\n\n"
        )
        message = f"""🎉 I am done learning docs in these directories:
        {dir_list} I am ready to answer questions about them.
        You can ask questions about these docs by prefixing your message with **/ask**."""
        self.reply(message)

    def create(self):
        embeddings = self.get_embedding_model()
        if not embeddings:
            return
        self.index = FAISS.from_texts(
            [
                "Jupyternaut knows about your filesystem, to ask questions first use the /learn command."
            ],
            embeddings,
        )
        self.save()

    def save(self):
        if self.index is not None:
            self.index.save_local(INDEX_SAVE_DIR, index_name=self.index_name)

        self.save_metadata()

    def save_metadata(self):
        with open(METADATA_SAVE_PATH, "w") as f:
            f.write(self.metadata.json())

    def load_or_create(self):
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
                self.create()

    def load_metadata(self):
        if not os.path.exists(METADATA_SAVE_PATH):
            return

        with open(METADATA_SAVE_PATH, encoding="utf-8") as f:
            j = json.loads(f.read())
            self.metadata = IndexMetadata(**j)

    def get_relevant_documents(self, question: str) -> List[Document]:
        if self.index:
            docs = self.index.similarity_search(question)
            return docs
        return []
    
    def aget_relevant_documents(self, query: str) -> Coroutine[Any, Any, List[Document]]:
        raise NotImplementedError()

    def get_embedding_model(self):
        em_provider = self.config_manager.get_em_provider()
        em_provider_params = self.config_manager.get_em_provider_params()
        curr_em_id = em_provider_params["model_id"]

        if not em_provider:
            return None

        if curr_em_id != self.prev_em_id:
            self.embeddings = em_provider(**em_provider_params)

        if self.prev_em_id != curr_em_id:
            if self.prev_em_id:
                # delete the index
                self.delete_and_relearn()

            # instantiate new embedding provider
            self.embeddings = em_provider(**em_provider_params)

        self.prev_em_id = curr_em_id
        return self.embeddings
