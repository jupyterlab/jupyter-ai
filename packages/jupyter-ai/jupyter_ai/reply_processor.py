import asyncio
from typing import Dict
from jupyter_ai.handlers import ChatHandler
from ray.util.queue import Queue


class ReplyProcessor():
    """A single processor to distribute replies"""

    def __init__(self, handlers: Dict[str, ChatHandler], queue: Queue, log):
        self.handlers = handlers
        self.queue = queue
        self.log = log

    def process(self, message):
        self.log.debug('Processing message %s in ReplyProcessor', message)
        for handler in self.handlers.values():
            if not handler:
                continue
            
            handler.broadcast_message(message)
            break

    async def start(self):
        while True:
            self.process(await self.queue.get_async())
