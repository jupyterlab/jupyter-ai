from typing import List

from jupyter_ai.models import ChatMessage, ClearMessage

from .base import BaseChatHandler


class ClearChatHandler(BaseChatHandler):
    id = "clear-chat-handler"
    name = "Clear chat messages"
    description = "Clear the chat message history display"
    help = "Clears the displayed chat message history only; does not clear the context sent to chat providers"
    slash_id = "clear"

    def __init__(self, chat_history: List[ChatMessage], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._chat_history = chat_history

    async def process_message(self, _):
        self._chat_history.clear()
        for handler in self._root_chat_handlers.values():
            if not handler:
                continue

            handler.broadcast_message(ClearMessage())
            break
