import argparse
from enum import Enum
from uuid import uuid4
import time
import logging
from typing import Union
import traceback

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
    
    def parse_args(self, message):
        args = message.body.split(' ')
        try:
            args = self.parser.parse_args(args[1:])
        except (argparse.ArgumentError, SystemExit) as e:
            response = f"{self.parser.format_usage()}"
            self.reply(response, message)
            return None
        return args