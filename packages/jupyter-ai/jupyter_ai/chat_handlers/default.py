import asyncio
from typing import Dict, Type

from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain_core.runnables import ConfigurableFieldSpec
from langchain_core.runnables.history import RunnableWithMessageHistory

from ..context_providers import ContextProviderException, find_commands
from .base import BaseChatHandler, SlashCommandRoutingType

class DefaultChatHandler(BaseChatHandler):
    id = "default"
    name = "Default"
    help = "Responds to prompts that are not otherwise handled by a chat handler"
    routing_type = SlashCommandRoutingType(slash_id=None)

    uses_llm = True
    supports_help = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt_template = None

    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        unified_parameters = {
            "verbose": True,
            **provider_params,
            **(self.get_model_parameters(provider, provider_params))
        }
        config = self.config_manager.get_config()

        if config.chat_prompt:
            if config.chat_prompt.system:
                unified_parameters["chat_system_prompt"] = config.chat_prompt.system
            if config.chat_prompt.default:
                unified_parameters["chat_default_prompt"] = config.chat_prompt.default

        if config.completion_prompt:
            if config.completion_prompt.system:
                unified_parameters["completion_system_prompt"] = config.chat_prompt.system
            if config.completion_prompt.default:
                unified_parameters["completion_default_prompt"] = config.chat_prompt.default


        llm = provider(
            **unified_parameters,
        )

        prompt_template = llm.get_chat_prompt_template()
        self.llm = llm
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
        self.get_llm_chain()
        assert self.llm_chain

        inputs = dict(
            input=message.body,
            selection=message.selection,
            notebook_code=self.llm.process_notebook_for_context(
                code_cells=[
                    cell.content for cell in message.notebook.notebook_code
                ] if message.notebook else [],
                active_cell=int(message.notebook.active_cell_id) if message.notebook.active_cell_id else None,
            ),
            active_cell_id=f"Cell {message.notebook.active_cell_id}" if message.notebook.active_cell_id else None,
            variable_context=message.notebook.variable_context or None
        )

        if "context" in self.prompt_template.input_variables:
            # include context from context providers.
            try:
                context_prompt = await self.make_context_prompt(message)
            except ContextProviderException as e:
                self.reply(str(e), message)
                return
            inputs["context"] = context_prompt
            inputs["input"] = self.replace_prompt(inputs["input"])

        history = self.llm_chat_memory.messages
        prompt = self.prompt_template.invoke(dict(inputs, history=history))
        extra_metadata = dict(
            prompt=prompt.to_string()
        )
        await self.stream_reply(inputs, message, extra_metadata=extra_metadata)

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
