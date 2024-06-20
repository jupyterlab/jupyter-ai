from typing import List

from jupyter_ai.models import ChatMessage, ClearMessage

from .base import BaseChatHandler, SlashCommandRoutingType


class ClearChatHandler(BaseChatHandler):
    """Clear the chat panel and show the help menu"""

    id = "clear"
    name = "Clear chat messages"
    help = "Clear the chat window"
    routing_type = SlashCommandRoutingType(slash_id="clear")

    uses_llm = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def process_message(self, _):
        tmp_chat_history = self._chat_history[0]
        self._chat_history.clear()
        for handler in self._root_chat_handlers.values():
            if not handler:
                continue

            handler.broadcast_message(ClearMessage())

            self._chat_history = [tmp_chat_history]
            self.reply(tmp_chat_history.body)

            break
