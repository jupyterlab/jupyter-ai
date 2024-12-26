from jupyter_ai.chat_handlers.base import BaseChatHandler, SlashCommandRoutingType
from jupyterlab_chat.models import Message


class TestSlashCommand(BaseChatHandler):
    """
    A test slash command implementation that developers should build from. The
    string used to invoke this command is set by the `slash_id` keyword argument
    in the `routing_type` attribute. The command is mainly implemented in the
    `process_message()` method. See built-in implementations under
    `jupyter_ai/handlers` for further reference.

    The provider is made available to Jupyter AI by the entry point declared in
    `pyproject.toml`. If this class or parent module is renamed, make sure the
    update the entry point there as well.
    """

    id = "test"
    name = "Test"
    help = "A test slash command."
    routing_type = SlashCommandRoutingType(slash_id="test")

    uses_llm = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def process_message(self, message: Message):
        self.reply("This is the `/test` slash command.")
