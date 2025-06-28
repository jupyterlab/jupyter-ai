from jupyter_ai.personas.base_persona import BasePersona, PersonaDefaults
from jupyterlab_chat.models import Message, NewMessage


class DebugPersona(BasePersona):
    """
    The Jupyternaut persona, the main persona provided by Jupyter AI.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def defaults(self):
        return PersonaDefaults(
            name="DebugPersona",
            avatar_path="/api/ai/static/jupyternaut.svg",
            description="A mock persona used for debugging in local dev environments.",
            system_prompt="...",
        )

    async def process_message(self, message: Message):
        self.send_message("Hola!")
