import time
from typing import List
from uuid import uuid4

from jupyter_ai.models import AgentChatMessage, HumanChatMessage

from .base import BaseChatHandler

CUSTOM_MESSAGE = "This handler displays a custom message in response to any prompt."


def CustomMessage():
    return AgentChatMessage(
        id=uuid4().hex,
        time=time.time(),
        body=CUSTOM_MESSAGE,
        reply_to="",
    )


"""
This is a sample custom chat handler class to demonstrate entry points.
"""


class CustomChatHandler(BaseChatHandler):
    id = "custom"
    name = "Custom"
    help = "Displays a custom message in the chat message area"
    routing_method = "slash_command"
    slash_id = "custom"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def _process_message(self, message: HumanChatMessage):
        self.reply(CUSTOM_MESSAGE, message)
