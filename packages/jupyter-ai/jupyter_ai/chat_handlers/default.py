import asyncio

from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain_core.output_parsers import StrOutputParser
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
        self, provider: type[BaseProvider], provider_params: dict[str, str]
    ):
        unified_parameters = {
            "verbose": True,
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        llm = provider(**unified_parameters)

        prompt_template = llm.get_chat_prompt_template()
        self.llm = llm
        self.prompt_template = prompt_template

        runnable = prompt_template | llm | StrOutputParser()  # type:ignore
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
