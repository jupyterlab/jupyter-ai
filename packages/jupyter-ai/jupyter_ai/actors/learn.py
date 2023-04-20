import os
import traceback
from collections import Counter
import argparse

import ray
from ray.util.queue import Queue

from jupyter_core.paths import jupyter_data_dir

from langchain import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter, PythonCodeTextSplitter,
    MarkdownTextSplitter, LatexTextSplitter
)

from jupyter_ai.models import HumanChatMessage
from jupyter_ai.actors.base import BaseActor, Logger
from jupyter_ai_magics.providers import ChatOpenAINewProvider
from jupyter_ai.document_loaders.directory import RayRecursiveDirectoryLoader
from jupyter_ai.document_loaders.splitter import ExtensionSplitter, NotebookSplitter


@ray.remote
class LearnActor(BaseActor):

    def __init__(self, reply_queue: Queue, log: Logger, root_dir: str):
        super().__init__(reply_queue=reply_queue, log=log)
        self.root_dir = root_dir
        self.index_save_dir = os.path.join(jupyter_data_dir(), 'jupyter_ai', 'indices')
        self.chunk_size = 2000
        self.chunk_overlap = 100
        self.parser.prog = '/learn'
        self.parser.add_argument('-v', '--verbose', action='store_true')
        self.parser.add_argument('-d', '--delete', action='store_true')
        self.parser.add_argument('path', nargs=argparse.REMAINDER)
        self.index_name = 'default'
        self.index = None

        if ChatOpenAINewProvider.auth_strategy.name not in os.environ:
            return
        
        if not os.path.exists(self.index_save_dir):
            os.makedirs(self.index_save_dir)

        self.load_or_create()
        
    def _process_message(self, message: HumanChatMessage):
        args = self.parse_args(message)
        if args is None:
            return

        if args.delete:
            self.delete()
            self.reply(f"👍 I have deleted everything I previously learned.", message)
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
        
        splitters={
            '.py': PythonCodeTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap),
            '.md': MarkdownTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap),
            '.tex': LatexTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap),
            '.ipynb': NotebookSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        }
        splitter = ExtensionSplitter(
            splitters=splitters,
            default_splitter=RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        )

        loader = RayRecursiveDirectoryLoader(load_path)
        texts = loader.load_and_split(text_splitter=splitter)        
        self.index.add_documents(texts)
        self.save()

        response = f"""🎉 I have indexed documents at **{load_path}** and I am ready to answer questions about them. 
        You can ask questions about these docs by prefixing your message with **/ask**."""
        self.reply(response, message)

    def get_index(self):
        return self.index

    def delete(self):
        self.index = None
        paths = [os.path.join(self.index_save_dir, self.index_name+ext) for ext in ['.pkl', '.faiss']]
        for path in paths:
            if os.path.isfile(path):
                os.remove(path)
        self.create()
    
    def create(self):
        embeddings = OpenAIEmbeddings()
        self.index = FAISS.from_texts(["Jupyter AI knows about your filesystem, to ask questions first use the /learn command."], embeddings)
        self.save()

    def save(self):
        if self.index is not None:
            self.index.save_local(self.index_save_dir, index_name=self.index_name)

    def load_or_create(self):
        embeddings = OpenAIEmbeddings()
        if self.index is None:
            try:
                self.index = FAISS.load_local(self.index_save_dir, embeddings, index_name=self.index_name)
            except Exception as e:
                self.create()
