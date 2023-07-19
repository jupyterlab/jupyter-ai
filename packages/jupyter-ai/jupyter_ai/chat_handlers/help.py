import time

from typing import List
from uuid import uuid4

from jupyter_ai.models import AgentChatMessage, ChatMessage

from .base import BaseChatHandler

HELP_MESSAGE = """Hi there! I'm Jupyternaut, your programming assistant. 
You can send me a message using the text box below. You can also send me commands:
* `/learn` — Teach Jupyternaut about files on your system
* `/ask` — Ask a question to be answered using learned data
* `/generate` — Generate a Jupyter notebook from a text prompt
* `/clear` — Clear the chat window
* `/help` — Display this help message

For more information about Jupyternaut, see the 
[Jupyter AI documentation](https://jupyter-ai.readthedocs.io).
"""

class HelpChatHandler(BaseChatHandler):
    def __init__(self, chat_history: List[ChatMessage], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._chat_history = chat_history

    async def _process_message(self, _):
        self._chat_history.clear()
        for handler in self._root_chat_handlers.values():
            if not handler:
                continue

            handler.broadcast_message(AgentChatMessage(
                id=uuid4().hex,
                time=time.time(),
                body=HELP_MESSAGE,
                reply_to="",
            ))
            break
