import time
from uuid import uuid4
from jupyter_ai.models import AgentChatMessage, HumanChatMessage
from langchain import FAISS
import ray
import os

from jupyter_ai.actors.base import BaseActor, Logger
from jupyter_ai_magics.providers import ChatOpenAINewProvider

from ray.util.queue import Queue
from jupyter_core.paths import jupyter_data_dir
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from jupyter_ai.document_loaders.directory import DirectoryLoader


@ray.remote
class DocumentIndexActor(BaseActor):
    def __init__(self, reply_queue: Queue, root_dir: str, log: Logger):
        super().__init__(log=log, reply_queue=reply_queue)
        self.root_dir = root_dir
        self.index_save_dir = os.path.join(jupyter_data_dir(), '.jupyter_ai_indexes')

        if ChatOpenAINewProvider.auth_strategy.name not in os.environ:
            return
        
        if not os.path.exists(self.index_save_dir):
            os.makedirs(self.index_save_dir)

        embeddings = OpenAIEmbeddings()
        try:
            self.index = FAISS.load_local(self.index_save_dir, embeddings)
        except Exception as e:
            self.index = FAISS.from_texts(["This is just starter text for the index"], embeddings)

    def get_index(self):
        return self.index

    def process_message(self, message: HumanChatMessage):
        dir_path = message.body.split(' ', 1)[-1]
        load_path = os.path.join(self.root_dir, dir_path)
        loader = DirectoryLoader(
            load_path, 
            glob=['*.txt', '*.text', '*.md', '*.py', '*.ipynb', '*.R'],
            loader_cls=TextLoader
        )
        documents = loader.load_and_split(
            text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
        )
        self.index.add_documents(documents)
        self.index.save_local(self.index_save_dir)

        response = f"""🎉 I have indexed documents at **{dir_path}** and ready to answer questions. 
        You can ask questions from these docs by prefixing your message with **/fs**."""
        agent_message = AgentChatMessage(
                id=uuid4().hex,
                time=time.time(),
                body=response,
                reply_to=message.id
            )
        self.reply_queue.put(agent_message)