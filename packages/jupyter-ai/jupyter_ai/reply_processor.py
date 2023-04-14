import asyncio
from typing import Dict
from jupyter_ai.handlers import ChatHandler
from ray.util.queue import Queue


class ReplyProcessor():
    """A single processor to distribute replies"""

    def __init__(self, handlers: Dict[str, ChatHandler], reply_queue: Queue, log):
        self.handlers = handlers
        self.reply_queue = reply_queue
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
            if not self.reply_queue.empty():
                self.process(self.reply_queue.get())
            
            await asyncio.sleep(5)
