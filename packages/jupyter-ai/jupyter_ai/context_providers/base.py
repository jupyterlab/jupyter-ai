import abc
import os
import re
from typing import TYPE_CHECKING, Awaitable, ClassVar, Dict, List, Optional

from dask.distributed import Client as DaskClient
from jupyter_ai.chat_handlers.base import get_preferred_dir
from jupyter_ai.config_manager import ConfigManager, Logger
from jupyter_ai.models import ChatMessage, HumanChatMessage, ListOptionsEntry
from langchain.pydantic_v1 import BaseModel

if TYPE_CHECKING:
    from jupyter_ai.chat_handlers import BaseChatHandler
    from jupyter_ai.history import BoundedChatHistory


class _BaseContextProvider(abc.ABC):
    id: ClassVar[str]
    """Unique identifier for the context provider command."""
    help: ClassVar[str]
    """What this chat handler does, which third-party models it contacts,
    the data it returns to the user, and so on, for display in the UI."""

    def __init__(
        self,
        *,
        log: Logger,
        config_manager: ConfigManager,
        model_parameters: Dict[str, Dict],
        chat_history: List[ChatMessage],
        llm_chat_memory: "BoundedChatHistory",
        root_dir: str,
        preferred_dir: Optional[str],
        dask_client_future: Awaitable[DaskClient],
        chat_handlers: Dict[str, "BaseChatHandler"],
        context_providers: Dict[str, "BaseCommandContextProvider"],
    ):
        preferred_dir = preferred_dir or ""
        self.log = log
        self.config_manager = config_manager
        self.model_parameters = model_parameters
        self._chat_history = chat_history
        self.llm_chat_memory = llm_chat_memory
        self.root_dir = os.path.abspath(os.path.expanduser(root_dir))
        self.preferred_dir = get_preferred_dir(self.root_dir, preferred_dir)
        self.dask_client_future = dask_client_future
        self.chat_handlers = chat_handlers
        self.context_providers = context_providers

        self.llm = None

    @abc.abstractmethod
    async def make_context_prompt(self, message: HumanChatMessage) -> str:
        """Returns a context prompt for all commands of the context provider
        command.
        """
        pass

    def replace_prompt(self, prompt: str) -> str:
        """Modifies the prompt before sending it to the LLM."""
        return prompt

    def _clean_prompt(self, text: str) -> str:
        # util for cleaning up the prompt before sending it to a retriever
        for provider in self.context_providers.values():
            text = provider.replace_prompt(text)
        return text

    @property
    def base_dir(self) -> str:
        # same as BaseChatHandler.output_dir
        if self.preferred_dir and os.path.exists(self.preferred_dir):
            return self.preferred_dir
        else:
            return self.root_dir

    def get_llm(self):
        lm_provider = self.config_manager.lm_provider
        lm_provider_params = self.config_manager.lm_provider_params

        curr_lm_id = (
            f'{self.llm.id}:{lm_provider_params["model_id"]}' if self.llm else None
        )
        next_lm_id = (
            f'{lm_provider.id}:{lm_provider_params["model_id"]}'
            if lm_provider
            else None
        )

        if not lm_provider or not lm_provider_params:
            return None

        if curr_lm_id != next_lm_id:
            model_parameters = self.model_parameters.get(
                f"{lm_provider.id}:{lm_provider_params['model_id']}", {}
            )
            unified_parameters = {
                "verbose": True,
                **lm_provider_params,
                **model_parameters,
            }
            llm = lm_provider(**unified_parameters)
            self.llm = llm
        return self.llm


class ContextCommand(BaseModel):
    cmd: str

    @property
    def id(self) -> str:
        return self.cmd.partition(":")[0]

    @property
    def arg(self) -> Optional[str]:
        if ":" not in self.cmd:
            return None
        return self.cmd.partition(":")[2].strip("'\"").replace("\\ ", " ")

    def __str__(self) -> str:
        return self.cmd

    def __hash__(self) -> int:
        return hash(self.cmd)


class BaseCommandContextProvider(_BaseContextProvider):
    id_prefix: ClassVar[str] = "@"
    """Prefix symbol for command. Generally should not be overridden."""

    # Configuration
    requires_arg: ClassVar[bool] = False
    """Whether command has an argument. E.g. '@file:<filepath>'."""
    remove_from_prompt: ClassVar[bool] = False
    """Whether the command should be removed from prompt when passing to LLM."""
    only_start: ClassVar[bool] = False
    """Whether to command can only be inserted at the start of the prompt."""

    @property
    def command_id(self) -> str:
        return self.id_prefix + self.id

    @property
    def pattern(self) -> str:
        # arg pattern allows for arguments between quotes or spaces with escape character ('\ ')
        return (
            rf"(?<![^\s.]){self.command_id}:(?:'[^']+'|\"[^\"]+\"|[^\s\\]+(?:\\ [^\s\\]*)*)"
            if self.requires_arg
            else rf"(?<![^\s.]){self.command_id}(?![^\s.])"
        )

    async def make_context_prompt(self, message: HumanChatMessage) -> str:
        """Returns a context prompt for all commands of the context provider
        command.
        """
        commands = find_commands(self, message.prompt)
        if not commands:
            return ""
        return await self._make_context_prompt(message, commands)

    @abc.abstractmethod
    async def _make_context_prompt(
        self, message: HumanChatMessage, commands: List[ContextCommand]
    ) -> str:
        """Returns a context prompt for the given commands."""
        pass

    def replace_prompt(self, prompt: str) -> str:
        """Cleans up commands from the prompt before sending it to the LLM"""

        def replace(match):
            if _is_command_call(match, prompt):
                return self._replace_command(ContextCommand(cmd=match.group()))
            return match.group()

        return re.sub(self.pattern, replace, prompt)

    def get_arg_options(self, arg_prefix: str) -> List[ListOptionsEntry]:
        """Returns a list of autocomplete options for arguments to the command
        based on the prefix.
        Only triggered if ':' is present after the command id (e.g. '@file:').
        """
        if self.requires_arg:
            # default implementation that should be modified if 'requires_arg' is True
            return [self._make_arg_option(arg_prefix)]
        return []

    def _replace_command(self, command: ContextCommand) -> str:
        if self.remove_from_prompt:
            return ""
        return command.cmd

    def _make_arg_option(
        self,
        arg: str,
        *,
        is_complete: bool = True,
        description: Optional[str] = None,
    ) -> ListOptionsEntry:
        arg = arg.replace("\\ ", " ").replace(" ", "\\ ")  # escape spaces
        label = self.command_id + ":" + arg + (" " if is_complete else "")
        return ListOptionsEntry(
            id=self.command_id,
            description=description or self.help,
            label=label,
            only_start=self.only_start,
        )


def find_commands(
    context_provider: BaseCommandContextProvider, text: str
) -> List[ContextCommand]:
    # finds commands of the context provider in the text
    matches = list(re.finditer(context_provider.pattern, text))
    if context_provider.only_start:
        matches = [match for match in matches if match.start() == 0]
    results = []
    for match in matches:
        if _is_command_call(match, text):
            results.append(ContextCommand(cmd=match.group()))
    return results


class ContextProviderException(Exception):
    # Used to generate a response when a context provider fails
    pass


def _is_command_call(match, text):
    """Check if the match is a command call rather than a part of a code block.
    This is done by checking if there is an even number of backticks before and
    after the match. If there is an odd number of backticks, the match is likely
    inside a code block.
    """
    # potentially buggy if there is a stray backtick in text
    # e.g. "help me count the backticks '`' ... ```\n...@cmd in code\n```".
    # can be addressed by having selection in context rather than in prompt.
    # more generally addressed by having a better command detection mechanism
    # such as placing commands within special tags.
    start, end = match.span()
    before = text[:start]
    after = text[end:]
    return before.count("`") % 2 == 0 or after.count("`") % 2 == 0
