from typing import List

from jupyter_ai.models import AgentChatMessage, HumanChatMessage

from .base import BaseChatHandler, SlashCommandRoutingType


class ExportChatHandler(BaseChatHandler):
    id = "export"
    name = "Export chat messages"
    help = "Export the chat messages in various formats"
    routing_type = SlashCommandRoutingType(slash_id="export")

    uses_llm = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def chat_message_to_markdown(self, message):
        if isinstance(message, AgentChatMessage):
            return f"**Agent**: {message.body}"
        elif isinstance(message, HumanChatMessage):
            return f"**{message.client.display_name}**: {message.body}"
        else:
            return ""

    async def process_message(self, _):
        markdown_content = "\n\n".join(
            self.chat_message_to_markdown(msg) for msg in self._chat_history
        )
        # Write the markdown content to a file or do whatever you want with it
        with open("./playground/chat_history.md", "w") as chat_history:
            chat_history.write(markdown_content)
