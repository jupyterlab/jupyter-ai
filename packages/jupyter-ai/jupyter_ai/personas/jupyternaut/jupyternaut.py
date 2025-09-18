from jupyterlab_chat.models import Message

from ..base_persona import BasePersona, PersonaDefaults
from ...default_flow import run_default_flow, DefaultFlowParams
from .prompt_template import (
    JUPYTERNAUT_SYSTEM_PROMPT_TEMPLATE,
    JupyternautSystemPromptArgs,
)
from ...tools import DEFAULT_TOOLKIT


class JupyternautPersona(BasePersona):
    """
    The Jupyternaut persona, the main persona provided by Jupyter AI.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def defaults(self):
        return PersonaDefaults(
            name="Jupyternaut",
            avatar_path="/api/ai/static/jupyternaut.svg",
            description="The standard agent provided by JupyterLab. Currently has no tools.",
            system_prompt="...",
        )

    async def process_message(self, message: Message) -> None:
        # Return early if no chat model is configured
        if not self.config_manager.chat_model:
            self.send_message(
                "No chat model is configured.\n\n"
                "You must set one first in the Jupyter AI settings, found in 'Settings > AI Settings' from the menu bar."
            )
            return

        # Build default flow params
        system_prompt = self._build_system_prompt(message)
        flow_params: DefaultFlowParams = {
            "persona_id": self.id,
            "model_id": self.config_manager.chat_model,
            "model_args": self.config_manager.chat_model_args,
            "ychat": self.ychat,
            "awareness": self.awareness,
            "system_prompt": system_prompt,
            "toolkit": DEFAULT_TOOLKIT,
            "logger": self.log,
        }

        # Run default agent flow
        await run_default_flow(flow_params)

    def _build_system_prompt(self, message: Message) -> str:
        context = self.process_attachments(message)
        format_args = JupyternautSystemPromptArgs(
            persona_name=self.name,
            model_id=self.config_manager.chat_model,
            context=context,
        )
        system_prompt = JUPYTERNAUT_SYSTEM_PROMPT_TEMPLATE.render(format_args.model_dump())
        return system_prompt