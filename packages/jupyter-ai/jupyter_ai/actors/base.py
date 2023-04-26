import argparse
from enum import Enum
from uuid import uuid4
import time
import logging
from typing import Dict, Union
import traceback

from jupyter_ai_magics.providers import BaseProvider
import ray

from ray.util.queue import Queue

from jupyter_ai.models import HumanChatMessage, AgentChatMessage

Logger = Union[logging.Logger, logging.LoggerAdapter]

class ACTOR_TYPE(str, Enum):
    DEFAULT = "default"
    ASK = "ask"
    LEARN = 'learn'
    MEMORY = 'memory'
    GENERATE = 'generate'
    PROVIDERS = 'providers'
    CONFIG = 'config'
    CHAT_PROVIDER = 'chat_provider'
    EMBEDDINGS_PROVIDER = 'embeddings_provider'

COMMANDS = {
    '/ask': ACTOR_TYPE.ASK,
    '/learn': ACTOR_TYPE.LEARN,
    '/generate': ACTOR_TYPE.GENERATE
}

class BaseActor():
    """Base actor implemented by actors that are called by the `Router`"""

    def __init__(
            self, 
            log: Logger,
            reply_queue: Queue
        ):
        self.log = log
        self.reply_queue = reply_queue
        self.parser = argparse.ArgumentParser()
        self.llm = None
        self.llm_params = None
        self.llm_chain = None
        self.embeddings = None
        self.embeddings_params = None

    def process_message(self, message: HumanChatMessage):
        """Processes the message passed by the `Router`"""
        try:
            self._process_message(message)
        except Exception as e:
            formatted_e = traceback.format_exc()
            response = f"Sorry, something went wrong and I wasn't able to index that path.\n\n```\n{formatted_e}\n```"
            self.reply(response, message)
    
    def _process_message(self, message: HumanChatMessage):
        """Processes the message passed by the `Router`"""
        raise NotImplementedError("Should be implemented by subclasses.")
    
    def reply(self, response, message: HumanChatMessage):
        m = AgentChatMessage(
            id=uuid4().hex,
            time=time.time(),
            body=response,
            reply_to=message.id
        )
        self.reply_queue.put(m)

    def get_llm_chain(self):
        actor = ray.get_actor(ACTOR_TYPE.CHAT_PROVIDER)
        handle = actor.get_provider.remote()
        llm = ray.get(handle)

        handle = actor.get_provider_params.remote()
        llm_params = ray.get(handle)

        if not llm:
            return None
        
        if llm.__class__.__name__ != self.llm.__class__.__name__:
            self.create_llm_chain(llm, llm_params)
        return self.llm_chain
    
    def get_embeddings(self):
        actor = ray.get_actor(ACTOR_TYPE.EMBEDDINGS_PROVIDER)
        handle = actor.get_provider.remote()
        provider = ray.get(handle)

        handle = actor.get_provider_params.remote()
        embedding_params = ray.get(handle)
        
        if not provider:
            return None
        if provider.__class__.__name__ != self.embeddings.__class__.__name__:
            self.embeddings = provider(**embedding_params)
        return self.embeddings
    
    def create_llm_chain(self, provider: BaseProvider, provider_params: Dict[str, str]):
        raise NotImplementedError("Should be implemented by subclasses")
    
    def parse_args(self, message):
        args = message.body.split(' ')
        try:
            args = self.parser.parse_args(args[1:])
        except (argparse.ArgumentError, SystemExit) as e:
            response = f"{self.parser.format_usage()}"
            self.reply(response, message)
            return None
        return args