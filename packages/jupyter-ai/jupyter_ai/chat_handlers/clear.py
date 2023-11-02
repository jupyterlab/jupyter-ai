from typing import List

from jupyter_ai.models import ChatMessage, ClearMessage

from .base import BaseChatHandler, SlashCommandRoutingType


class ClearChatHandler(BaseChatHandler):
    id = "clear"
    name = "Clear chat messages"
    help = "Clears the displayed chat message history only; does not clear the context sent to chat providers"
    routing_type = SlashCommandRoutingType(slash_id="clear")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def process_message(self, _):
        self._chat_history.clear()
        for handler in self._root_chat_handlers.values():
            if not handler:
                continue

            handler.broadcast_message(ClearMessage())
            break
