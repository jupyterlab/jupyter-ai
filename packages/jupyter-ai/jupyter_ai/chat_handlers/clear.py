from typing import List

from jupyter_ai.models import ChatMessage, ClearMessage

from .base import BaseChatHandler


class ClearChatHandler(BaseChatHandler):
    def __init__(self, chat_history: List[ChatMessage], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._chat_history = chat_history

    async def _process_message(self, _):
        self._chat_history.clear()
        for handler in self._root_chat_handlers.values():
            if not handler:
                continue

            handler.broadcast_message(ClearMessage())
            break
