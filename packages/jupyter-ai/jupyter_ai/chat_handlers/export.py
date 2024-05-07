import os
from datetime import datetime
from typing import List

from jupyter_ai.models import AgentChatMessage, HumanChatMessage

from .base import BaseChatHandler, SlashCommandRoutingType


class ExportChatHandler(BaseChatHandler):
    id = "export"
    name = "Export chat messages"
    help = "Export the chat messages in markdown format with timestamps"
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

    # Multiple chat histories can be saved in separate files, each with a timestamp
    def get_chat_filename(self, file_id):
        file_id = file_id.split(" ")
        if len(file_id) > 1:
            file_id = file_id[-1]
        else:
            file_id = "chat_history"
        outfile = f"{file_id}-{datetime.now():%Y-%m-%d-%H-%M}.md"
        path = os.path.join(self.root_dir, outfile)
        return path

    async def process_message(self, _):
        markdown_content = "\n\n".join(
            self.chat_message_to_markdown(msg) for msg in self._chat_history
        )
        # Write the markdown content to a file or do whatever you want with it
        chat_filename = self.get_chat_filename(self._chat_history[-1].body)
        with open(chat_filename, "w") as chat_history:
            chat_history.write(markdown_content)

        self.reply(f"File saved to `{chat_filename}`")
