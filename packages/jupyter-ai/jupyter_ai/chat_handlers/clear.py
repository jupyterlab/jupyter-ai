from typing import List

from jupyter_ai.chat_handlers.help import build_help_message
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
        for handler in self._root_chat_handlers.values():
            if not handler:
                continue

            # Clear chat
            handler.broadcast_message(ClearMessage())
            self._chat_history.clear()

            # Build /help message and reinstate it in chat
            chat_handlers = handler.chat_handlers
            persona = self.config_manager.persona
            lm_provider = self.config_manager.lm_provider
            unsupported_slash_commands = (
                lm_provider.unsupported_slash_commands if lm_provider else set()
            )
            msg = build_help_message(chat_handlers, persona, unsupported_slash_commands)
            self.reply(msg.body)

            break
