import time
from uuid import uuid4
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

from jupyter_ai.models import AgentChatMessage, HumanChatMessage
from jupyter_ai.actors.base import BaseActor, Logger
from jupyter_ai_magics.providers import ChatOpenAINewProvider
from jupyter_ai.document_loaders.directory import RayRecursiveDirectoryLoader
from jupyter_ai.document_loaders.splitter import ExtensionSplitter, NotebookSplitter


def create_message(response, id):
    m = AgentChatMessage(
        id=uuid4().hex,
        time=time.time(),
        body=response,
        reply_to=id
    )
    return m

@ray.remote
class DocumentIndexActor(BaseActor):

    def __init__(self, reply_queue: Queue, root_dir: str, log: Logger):
        super().__init__(log=log, reply_queue=reply_queue)
        self.root_dir = root_dir
        self.index_save_dir = os.path.join(jupyter_data_dir(), '.jupyter_ai_indexes')
        self.chunk_size = 2000
        self.chunk_overlap = 100
        self.parser = argparse.ArgumentParser(prog='/index')
        self.parser.add_argument('path')
        self.parser.add_argument('-v', '--verbose', action='store_true')

        if ChatOpenAINewProvider.auth_strategy.name not in os.environ:
            return
        
        if not os.path.exists(self.index_save_dir):
            os.makedirs(self.index_save_dir)

        embeddings = OpenAIEmbeddings()
        try:
            self.index = FAISS.load_local(self.index_save_dir, embeddings)
        except Exception as e:
            self.index = FAISS.from_texts(["Jupyter AI knows about your filesystem, to ask questions first use the /index command."], embeddings)

    def get_index(self):
        return self.index
        
    def process_message(self, message: HumanChatMessage):

        def reply(response):
            m = create_message(response, message.id)
            self.reply_queue.put(m)

        try:
            args = message.body.split(' ')

            if len(args) <= 1:
                response = f"Usage: `/index [-v] path`."
                reply(response)
                return
            
            try:
                args = self.parser.parse_args(args[1:])
            except (argparse.ArgumentError, SystemExit) as e:
                response = f"Usage: `/index [-v] path`."
                reply(response)
                return

            load_path = os.path.join(self.root_dir, args.path)

            # Make sure the path exists.
            if not os.path.exists(load_path):
                response = f"Sorry, that path doesn't exist: {load_path}"
                reply(response)
                return

            if args.verbose:
                reply(f"Loading and splitting files for {load_path}")
            
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

            counts = Counter([text.metadata['extension'] for text in texts])
            if args.verbose:
                reply(f"I have read the files from {load_path} and processed them into {sum(counts.values())} total chunks.")
            
            self.index.add_documents(texts)
            self.index.save_local(self.index_save_dir)

            response = f"""🎉 I have indexed documents at **{args.path}** and ready to answer questions. 
            You can ask questions from these docs by prefixing your message with **/fs**."""
            reply(response)
        except Exception as e:
            formatted_e = traceback.format_exc()
            response = f"Sorry, something went wrong and I wasn't able to index that path.\n\n```\n{formatted_e}\n```"
            reply(response)