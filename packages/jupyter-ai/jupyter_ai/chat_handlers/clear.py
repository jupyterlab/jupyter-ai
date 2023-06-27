from jupyter_ai.models import HumanChatMessage
from .base import BaseChatHandler
from jupyter_ai.models import ClearMessage

class ClearChatHandler(BaseChatHandler):
    def _process_message(self, message: HumanChatMessage):
        m = ClearMessage()
        self.reply(m)