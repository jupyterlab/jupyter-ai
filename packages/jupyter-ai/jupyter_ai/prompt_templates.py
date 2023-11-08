from traitlets import Dict, Unicode
from traitlets.config import Configurable

SYSTEM_TEMPLATE = """
You are Jupyternaut, a conversational assistant living in JupyterLab to help users.
You are not a language model, but rather an application built on a foundation model from {provider_name} called {local_model_id}.
You are talkative and you provide lots of specific details from the foundation model's context.
You may use Markdown to format your response.
Code blocks must be formatted in Markdown.
Math should be rendered with inline TeX markup, surrounded by $.
If you do not know the answer to a question, answer truthfully by responding that you do not know.
The following is a friendly conversation between you and a human.
""".strip()

HISTORY_TEMPLATE = """
Current conversation:
{history}
Human: {input}
AI:
""".strip()


class ChatPromptTemplates(Configurable):
    system_template = Unicode(
        default_value=SYSTEM_TEMPLATE,
        help="The system prompt template.",
        allow_none=False,
        config=True,
    )

    system_overrides = Dict(
        key_trait=Unicode(),
        value_trait=Unicode(),
        default_value={},
        help="Defines model-specific overrides of the system prompt template.",
        allow_none=False,
        config=True,
    )

    history_template = Unicode(
        default_value=HISTORY_TEMPLATE,
        help="The history prompt template.",
        allow_none=False,
        config=True,
    )

    history_overrides = Dict(
        key_trait=Unicode(),
        value_trait=Unicode(),
        default_value={},
        help="Defines model-specific overrides of the history prompt template.",
        allow_none=False,
        config=True,
    )

    lm_id: str = None

    def __init__(self, lm_id, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def system(self) -> str:
        return self.system_overrides.get(self.lm_id, self.system_template)

    @property
    def history(self) -> str:
        return self.history_overrides.get(self.lm_id, self.history_template)


class AskPromptTemplates(Configurable):
    ...


class GeneratePromptTemplates(Configurable):
    ...
