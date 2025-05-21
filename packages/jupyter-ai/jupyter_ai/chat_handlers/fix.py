from jupyter_ai.models import CellWithErrorSelection, HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .base import BaseChatHandler, SlashCommandRoutingType

FIX_STRING_TEMPLATE = """
You are Jupyternaut, a conversational assistant living in JupyterLab. Please fix
the notebook cell described below.

Additional instructions:

{extra_instructions}

Input cell:

```
{cell_content}
```

Output error:

```
{traceback}

{error_name}: {error_value}
```
""".strip()

FIX_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=[
        "extra_instructions",
        "cell_content",
        "traceback",
        "error_name",
        "error_value",
    ],
    template=FIX_STRING_TEMPLATE,
)


class FixChatHandler(BaseChatHandler):
    """
    Accepts a `HumanChatMessage` that includes a cell with error output and
    recommends a fix as a reply. If a cell with error output is not included,
    this chat handler does nothing.

    `/fix` also accepts additional instructions in natural language as an
    arbitrary number of arguments, e.g.

    ```
    /fix use the numpy library to implement this function instead.
    ```
    """

    id = "fix"
    name = "Fix error cell"
    help = "Fix an error cell selected in your notebook"
    routing_type = SlashCommandRoutingType(slash_id="fix")
    uses_llm = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt_template = None

    def create_llm_chain(
        self, provider: type[BaseProvider], provider_params: dict[str, str]
    ):
        unified_parameters = {
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        llm = provider(**unified_parameters)
        self.llm = llm
        prompt_template = FIX_PROMPT_TEMPLATE

        runnable = prompt_template | llm | StrOutputParser()  # type:ignore
        self.llm_chain = runnable

    async def process_message(self, message: HumanChatMessage):
        if not (message.selection and message.selection.type == "cell-with-error"):
            self.reply(
                "`/fix` requires an active code cell with error output. Please click on a cell with error output and retry.",
                message,
            )
            return

        # hint type of selection
        selection: CellWithErrorSelection = message.selection

        # parse additional instructions specified after `/fix`
        extra_instructions = message.prompt[4:].strip() or "None."

        self.get_llm_chain()
        assert self.llm_chain

        inputs = {
            "extra_instructions": extra_instructions,
            "cell_content": selection.source,
            "traceback": "\n".join(selection.error.traceback),
            "error_name": selection.error.name,
            "error_value": selection.error.value,
        }
        await self.stream_reply(inputs, message, pending_msg="Analyzing error")
