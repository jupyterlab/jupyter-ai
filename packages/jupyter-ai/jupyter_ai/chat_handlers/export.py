import argparse
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
        self.parser.prog = "/export"
        self.parser.add_argument("path", nargs=argparse.REMAINDER)

    def chat_message_to_markdown(self, message):
        if isinstance(message, AgentChatMessage):
            return f"**Agent**: {message.body}"
        elif isinstance(message, HumanChatMessage):
            return f"**{message.client.display_name}**: {message.body}"
        else:
            return ""

    # Write the chat history to a markdown file with a timestamp
    async def process_message(self, message: HumanChatMessage):
        markdown_content = "\n\n".join(
            self.chat_message_to_markdown(msg) for msg in self._chat_history
        )
        args = self.parse_args(message)
        chat_filename = args.path[0] if args.path else "chat_history"
        chat_filename = f"{chat_filename}-{datetime.now():%Y-%m-%d-%H-%M}.md"
        chat_file = os.path.join(self.root_dir, chat_filename)
        with open(chat_file, "w") as chat_history:
            chat_history.write(markdown_content)
        self.reply(f"File saved to `{chat_file}`")
