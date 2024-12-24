from jupyterlab_chat.models import Message

from .base import BaseChatHandler, SlashCommandRoutingType


class HelpChatHandler(BaseChatHandler):
    id = "help"
    name = "Help"
    help = "Display this help message"
    routing_type = SlashCommandRoutingType(slash_id="help")
    supports_help = False

    uses_llm = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def process_message(self, message: Message):
        self.send_help_message(message)
