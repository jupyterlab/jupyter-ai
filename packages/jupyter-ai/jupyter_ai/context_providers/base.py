import abc
import re
from typing import ClassVar, List

import os
from typing import (
    TYPE_CHECKING,
    Awaitable,
    ClassVar,
    Dict,
    List,
    Optional,
)

from dask.distributed import Client as DaskClient
from jupyter_ai.config_manager import ConfigManager, Logger
from jupyter_ai.models import (
    ChatMessage,
    HumanChatMessage,
)
from jupyter_ai.chat_handlers.base import get_preferred_dir
from jupyter_ai.models import ListOptionsEntry, HumanChatMessage

if TYPE_CHECKING:
    from jupyter_ai.history import BoundedChatHistory
    from jupyter_ai.chat_handlers import BaseChatHandler


class BaseContextProvider(abc.ABC):
    id: ClassVar[str]
    description: ClassVar[str]

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
        context_providers: Dict[str, "BaseContextProvider"],
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
        """Returns a context prompt for all instances of the context provider
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


class BaseCommandContextProvider(BaseContextProvider):
    requires_arg: ClassVar[bool] = False
    remove_from_prompt: ClassVar[bool] = (
        False  # whether the command should be removed from prompt
    )

    @property
    def pattern(self) -> str:
        return (
            rf"(?<![^\s.])@{self.id}:[^\s]+"
            if self.requires_arg
            else rf"(?<![^\s.])@{self.id}(?![^\s.])"
        )

    def replace_prompt(self, prompt: str) -> str:
        """Cleans up instances of the command from the prompt before
        sending it to the LLM
        """

        def replace(match):
            if _is_within_backticks(match, prompt):
                return match.group()
            return self._replace_instance(match.group())

        return re.sub(self.pattern, replace, prompt)

    def get_arg_options(self, arg_prefix: str) -> List[ListOptionsEntry]:
        """Returns a list of autocomplete options for arguments to the command
        based on the prefix.
        Only triggered if ':' is present after the command id (e.g. '@file:').
        """
        if self.requires_arg:
            # default implementation that should be modified if 'requires_arg' is True
            return [
                ListOptionsEntry.from_arg(
                    type="@",
                    id=self.id,
                    description=self.description,
                    arg=arg_prefix,
                    is_complete=True,
                )
            ]
        return []

    def _find_instances(self, text: str) -> List[str]:
        # finds instances of the context provider command in the text
        matches = re.finditer(self.pattern, text)
        results = []
        for match in matches:
            if not _is_within_backticks(match, text):
                results.append(match.group())
        return results

    def _replace_instance(self, instance: str) -> str:
        if self.remove_from_prompt:
            return ""
        return instance


def _is_within_backticks(match, text):
    # potentially buggy if there is a stray backtick in text
    # e.g. "help me count the backticks '`' in @file:file.txt".
    # better addressed by having a better instance detection mechanism
    # such as placing commands with special tags.
    start, _ = match.span()
    before = text[:start]
    return before.count("`") % 2 == 1


class ContextProviderException(Exception):
    # Used to generate a response when a context provider fails
    pass
