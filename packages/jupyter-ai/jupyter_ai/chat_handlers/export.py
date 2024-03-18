import os
from typing import List

from jupyter_ai.models import AgentChatMessage, HumanChatMessage

from .base import BaseChatHandler, SlashCommandRoutingType


class ExportChatHandler(BaseChatHandler):
    id = "export"
    name = "Export chat messages"
    help = "Export the chat messages in markdown format"
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

    # Multiple chat histories in separate files
    def get_chat_filename(self, path="./chat_history.md"):
        filename, extension = os.path.splitext(path)
        counter = 1
        while os.path.exists(path):
            path = filename + "_" + str(counter) + ".md"
            counter += 1
        return path

    async def process_message(self, _):
        markdown_content = "\n\n".join(
            self.chat_message_to_markdown(msg) for msg in self._chat_history
        )
        # Write the markdown content to a file or do whatever you want with it
        chat_filename = self.get_chat_filename()
        with open(chat_filename, "w") as chat_history:
            chat_history.write(markdown_content)

        self.reply(f"File saved to `{chat_filename}`")
