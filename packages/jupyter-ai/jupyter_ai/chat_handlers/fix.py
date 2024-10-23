import asyncio
from typing import Dict, Type

from jupyter_ai.models import CellWithErrorSelection, HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.prompts import PromptTemplate
from langchain_core.runnables import ConfigurableFieldSpec
from langchain_core.runnables.history import RunnableWithMessageHistory

from ..context_providers import ContextProviderException, find_commands
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
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        unified_parameters = {
            "verbose": True,
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        llm = provider(**unified_parameters)
        self.llm = llm
        prompt_template = llm.get_chat_prompt_template()
        self.prompt_template = prompt_template

        runnable = prompt_template | llm  # type:ignore
        if not llm.manages_history:
            runnable = RunnableWithMessageHistory(
                runnable=runnable,  #  type:ignore[arg-type]
                get_session_history=self.get_llm_chat_memory,
                input_messages_key="input",
                history_messages_key="history",
                history_factory_config=[
                    ConfigurableFieldSpec(
                        id="last_human_msg",
                        annotation=HumanChatMessage,
                    ),
                ],
            )
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

        inputs = {"input": message.body}
        if "context" in self.prompt_template.input_variables:
            # include context from context providers.
            try:
                context_prompt = await self.make_context_prompt(message)
            except ContextProviderException as e:
                self.reply(str(e), message)
                return
            inputs["context"] = context_prompt
            inputs["input"] = self.replace_prompt(inputs["input"])

        await self.stream_reply(inputs, message)

    async def make_context_prompt(self, human_msg: HumanChatMessage) -> str:
        return "\n\n".join(
            await asyncio.gather(
                *[
                    provider.make_context_prompt(human_msg)
                    for provider in self.context_providers.values()
                    if find_commands(provider, human_msg.prompt)
                ]
            )
        )

    def replace_prompt(self, prompt: str) -> str:
        # modifies prompt by the context providers.
        # some providers may modify or remove their '@' commands from the prompt.
        for provider in self.context_providers.values():
            prompt = provider.replace_prompt(prompt)
        return prompt
