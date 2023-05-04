import argparse
from enum import Enum
from uuid import uuid4
import time
import logging
from typing import Dict, Optional, Type, Union
import traceback

from jupyter_ai_magics.providers import BaseProvider
import ray

from ray.util.queue import Queue

from jupyter_ai.models import HumanChatMessage, AgentChatMessage

Logger = Union[logging.Logger, logging.LoggerAdapter]

class ACTOR_TYPE(str, Enum):
    # the top level actor that routes incoming messages to the appropriate actor
    ROUTER = "router"

    # the default actor that responds to messages using a language model
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
        self.embedding_model_id = None

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
    
    def reply(self, response, message: Optional[HumanChatMessage] = None):
        m = AgentChatMessage(
            id=uuid4().hex,
            time=time.time(),
            body=response,
            reply_to=message.id if message else ""
        )
        self.reply_queue.put(m)

    def get_llm_chain(self):
        actor = ray.get_actor(ACTOR_TYPE.CHAT_PROVIDER)
        lm_provider = ray.get(actor.get_provider.remote())
        lm_provider_params = ray.get(actor.get_provider_params.remote())

        curr_lm_id = f'{self.llm.id}:{lm_provider_params["model_id"]}' if self.llm else None
        next_lm_id = f'{lm_provider.id}:{lm_provider_params["model_id"]}' if lm_provider else None

        if not lm_provider:
            return None
        
        if curr_lm_id != next_lm_id:
            self.log.info(f"Switching chat language model from {curr_lm_id} to {next_lm_id}.")
            self.create_llm_chain(lm_provider, lm_provider_params)
        return self.llm_chain
    
    def get_embeddings(self):
        actor = ray.get_actor(ACTOR_TYPE.EMBEDDINGS_PROVIDER)
        provider = ray.get(actor.get_provider.remote())
        embedding_params = ray.get(actor.get_provider_params.remote())
        embedding_model_id = ray.get(actor.get_model_id.remote())
        
        if not provider:
            return None
        
        if embedding_model_id != self.embedding_model_id:
            self.embeddings = provider(**embedding_params)

        return self.embeddings
    
    def create_llm_chain(self, provider: Type[BaseProvider], provider_params: Dict[str, str]):
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