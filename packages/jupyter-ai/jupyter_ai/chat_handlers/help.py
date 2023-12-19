import time
from typing import Dict
from uuid import uuid4

from jupyter_ai.models import AgentChatMessage, HumanChatMessage

from .base import BaseChatHandler, SlashCommandRoutingType

HELP_MESSAGE = """Hi there! I'm Jupyternaut, your programming assistant.
You can ask me a question using the text box below. You can also use these commands:
{commands}

Jupyter AI includes [magic commands](https://jupyter-ai.readthedocs.io/en/latest/users/index.html#the-ai-and-ai-magic-commands) that you can use in your notebooks.
For more information, see the [documentation](https://jupyter-ai.readthedocs.io).
"""


def _format_help_message(chat_handlers: Dict[str, BaseChatHandler]):
    commands = "\n".join(
        [
            f"* `{command_name}` — {handler.help}"
            for command_name, handler in chat_handlers.items()
            if command_name != "default"
        ]
    )
    return HELP_MESSAGE.format(commands=commands)


def HelpMessage(chat_handlers: Dict[str, BaseChatHandler]):
    return AgentChatMessage(
        id=uuid4().hex,
        time=time.time(),
        body=_format_help_message(chat_handlers),
        reply_to="",
    )


class HelpChatHandler(BaseChatHandler):
    id = "help"
    name = "Help"
    help = "Display this help message"
    routing_type = SlashCommandRoutingType(slash_id="help")

    uses_llm = False

    def __init__(self, *args, chat_handlers: Dict[str, BaseChatHandler], **kwargs):
        super().__init__(*args, **kwargs)
        self._chat_handlers = chat_handlers

    async def process_message(self, message: HumanChatMessage):
        self.reply(_format_help_message(self._chat_handlers), message)
