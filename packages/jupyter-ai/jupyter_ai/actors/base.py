from enum import Enum
import logging
from typing import Union
from jupyter_ai.models import HumanChatMessage
from ray.util.queue import Queue


Logger = Union[logging.Logger, logging.LoggerAdapter]

class ACTOR_TYPE(str, Enum):
    DEFAULT = "default"
    ASK = "ask"
    LEARN = 'learn'
    MEMORY = 'memory'

COMMANDS = {
    '/ask': ACTOR_TYPE.ASK,
    '/learn': ACTOR_TYPE.LEARN
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

    def process_message(self, message: HumanChatMessage):
        """Processes the message passed by the `Router`"""
        raise NotImplementedError("Should be implemented by subclasses.")