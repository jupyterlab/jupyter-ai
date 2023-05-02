import json
import os
import argparse
import time
from typing import List

import ray
from ray.util.queue import Queue

from jupyter_core.paths import jupyter_data_dir

from langchain import FAISS
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter, PythonCodeTextSplitter,
    MarkdownTextSplitter, LatexTextSplitter
)
from langchain.schema import Document

from jupyter_ai.models import HumanChatMessage, IndexedDir, IndexMetadata
from jupyter_ai.actors.base import BaseActor, Logger
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
        self.parser.add_argument('-l', '--list', action='store_true')
        self.parser.add_argument('path', nargs=argparse.REMAINDER)
        self.index_name = 'default'
        self.index = None
        self.metadata = IndexMetadata(dirs=[])
        self.metadata_save_path = os.path.join(self.index_save_dir, 'metadata.json')
 
        if not os.path.exists(self.index_save_dir):
            os.makedirs(self.index_save_dir)
        
        self.load_or_create()    
        
    def _process_message(self, message: HumanChatMessage):
        if not self.index:
            self.load_or_create()

        # If index is not still there, embeddings are not present
        if not self.index:
            self.reply("Sorry, please select an embedding provider before using the `/learn` command.")

        args = self.parse_args(message)
        if args is None:
            return

        if args.delete:
            self.delete()
            self.reply(f"👍 I have deleted everything I previously learned.", message)
            return
        
        if args.list:
            self.reply(self.build_list_response())
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

    def build_list_response(self):
        if not self.metadata.dirs:
            return "There are no docs that have been learned yet."
        
        dirs = [dir.path for dir in self.metadata.dirs]
        dir_list = "\n- " + "\n- ".join(dirs) + "\n\n"
        message = f"""I can answer questions from docs in these directories:
        {dir_list}"""
        return message

    def learn_dir(self, path: str):
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

        loader = RayRecursiveDirectoryLoader(path)
        texts = loader.load_and_split(text_splitter=splitter)
        self.index.add_documents(texts)
        self.add_dir_to_metadata(path)
    
    def add_dir_to_metadata(self, path: str):
        dirs = self.metadata.dirs
        index = next((i for i, dir in enumerate(dirs) if dir.path == path), None)
        meta = IndexedDir(path=path)
        if index:
            dirs[index] = meta
        else:
            dirs.append(meta)
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
        paths = [os.path.join(self.index_save_dir, self.index_name+ext) for ext in ['.pkl', '.faiss']]
        for path in paths:
            if os.path.isfile(path):
                os.remove(path)
        self.create()

    def relearn(self, metadata: IndexMetadata):
        # Index all dirs in the metadata
        if not metadata.dirs:
            return    
        dirs = []
        for dir in metadata.dirs:
            self.learn_dir(dir.path)
            dirs.append(dir.path)

        self.save()

        dir_list = "\n- " + "\n- ".join(dirs) + "\n\n"
        message = f"""🎉 I am done learning docs in these directories:
        {dir_list} I am ready to answer questions about them. 
        You can ask questions about these docs by prefixing your message with **/ask**."""
        self.reply(message)

    def create(self):
        embeddings = self.get_embeddings()
        if not embeddings:
            return
        self.index = FAISS.from_texts(["Jupyter AI knows about your filesystem, to ask questions first use the /learn command."], embeddings)
        self.save()

    def save(self):
        if self.index is not None:
            self.index.save_local(self.index_save_dir, index_name=self.index_name)
        
        self.save_metdata()

    def save_metdata(self):
        with open(self.metadata_save_path, 'w') as f:
            f.write(self.metadata.json())

    def load_or_create(self):
        embeddings = self.get_embeddings()
        if not embeddings:
            return
        if self.index is None:
            try:
                self.index = FAISS.load_local(self.index_save_dir, embeddings, index_name=self.index_name)
                self.load_metadata()
            except Exception as e:
                self.create()

    def load_metadata(self):
        if not os.path.exists(self.metadata_save_path):
           return
        
        with open(self.metadata_save_path, 'r', encoding='utf-8') as f:
            j = json.loads(f.read()) 
            self.metadata = IndexMetadata(**j)

    def get_relevant_documents(self, question: str) -> List[Document]:
        if self.index:
            docs = self.index.similarity_search(question)
            return docs
        return []
