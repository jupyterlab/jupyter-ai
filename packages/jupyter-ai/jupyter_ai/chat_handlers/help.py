import time
from typing import List
from uuid import uuid4

from jupyter_ai.models import AgentChatMessage, HumanChatMessage

from .base import BaseChatHandler, SlashCommandRoutingType

HELP_MESSAGE = """Hi there! I'm Jupyternaut, your programming assistant.
You can ask me a question using the text box below. You can also use these commands:
* `/learn` — Teach Jupyternaut about files on your system
* `/ask` — Ask a question about your learned data
* `/generate` — Generate a Jupyter notebook from a text prompt
* `/clear` — Clear the chat window
* `/help` — Display this help message

Jupyter AI includes [magic commands](https://jupyter-ai.readthedocs.io/en/latest/users/index.html#the-ai-and-ai-magic-commands) that you can use in your notebooks.
For more information, see the [documentation](https://jupyter-ai.readthedocs.io).
"""


def HelpMessage():
    return AgentChatMessage(
        id=uuid4().hex,
        time=time.time(),
        body=HELP_MESSAGE,
        reply_to="",
    )


class HelpChatHandler(BaseChatHandler):
    id = "help"
    name = "Help"
    help = "Displays a help message in the chat message area"
    routing_type = SlashCommandRoutingType(slash_id="help")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def process_message(self, message: HumanChatMessage):
        self.reply(HELP_MESSAGE, message)
