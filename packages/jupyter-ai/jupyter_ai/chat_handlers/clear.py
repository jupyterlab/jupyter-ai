from .base import BaseChatHandler
from jupyter_ai.models import ClearMessage

class ClearChatHandler(BaseChatHandler):
    async def _process_message(self, _):
        for handler in self._root_chat_handlers.values():
            if not handler:
                continue

            handler.broadcast_message(ClearMessage())
            break
    