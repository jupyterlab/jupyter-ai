import argparse
import os
from datetime import datetime
from typing import List

from jupyter_ai.models import AgentChatMessage, HumanChatMessage

from .base import BaseChatHandler, SlashCommandRoutingType


class ExportChatHandler(BaseChatHandler):
    id = "export"
    name = "Export chat history"
    help = "Export chat history to a Markdown file"
    routing_type = SlashCommandRoutingType(slash_id="export")

    uses_llm = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser.prog = "/export"
        self.parser.add_argument("path", nargs=argparse.REMAINDER)

    def chat_message_to_markdown(self, message):
        if isinstance(message, AgentChatMessage):
            agent = self.config_manager.persona.name
            return f"**{agent}**: {message.body}"
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
        chat_filename = (  # if no filename, use "chat_history" + timestamp
            args.path[0]
            if (args.path and args.path[0] != "")
            else f"chat_history-{datetime.now():%Y-%m-%d-%H-%M-%S}.md"
        )  # Handles both empty args and double tap <Enter> key
        chat_file = os.path.join(
            self.output_dir, chat_filename
        )  # Do not use timestamp if filename is entered as argument
        with open(chat_file, "w") as chat_history:
            chat_history.write(markdown_content)
        self.reply(f"File saved to `{chat_file}`")
