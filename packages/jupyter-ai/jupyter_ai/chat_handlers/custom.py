from jupyter_ai.models import HumanChatMessage

from .base import BaseChatHandler

CUSTOM_MESSAGE = "This handler displays a custom message in response to any prompt."


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
