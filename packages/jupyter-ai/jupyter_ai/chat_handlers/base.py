import argparse
import time
import traceback

# necessary to prevent circular import
from typing import TYPE_CHECKING, Dict, Optional, Type
from uuid import uuid4

from jupyter_ai.config_manager import ConfigManager, Logger
from jupyter_ai.models import AgentChatMessage, HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from traitlets.config import Configurable

if TYPE_CHECKING:
    from jupyter_ai.handlers import RootChatHandler


class BaseChatHandler(Configurable):
    """Base ChatHandler class containing shared methods and attributes used by
    multiple chat handler classes."""

    def __init__(
        self,
        log: Logger,
        config_manager: ConfigManager,
        root_chat_handlers: Dict[str, "RootChatHandler"],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.log = log
        self.config_manager = config_manager
        self._root_chat_handlers = root_chat_handlers
        self.parser = argparse.ArgumentParser()
        self.llm = None
        self.llm_params = None
        self.llm_chain = None

    async def on_message(self, message: HumanChatMessage):
        """
        Method which receives a human message and processes it via
        `self.process_message()`, calling `self.handle_exc()` when an exception
        is raised. This method is called by RootChatHandler when it routes a
        human message to this chat handler.
        """
        try:
            await self.process_message(message)
        except Exception as e:
            try:
                # we try/except `handle_exc()` in case it was overriden and
                # raises an exception by accident.
                await self.handle_exc(e, message)
            except Exception as e:
                await self._default_handle_exc(e, message)

    async def process_message(self, message: HumanChatMessage):
        """
        Processes a human message routed to this chat handler. Chat handlers
        (subclasses) must implement this method. Don't forget to call
        `self.reply(<response>, message)` at the end!

        The method definition does not need to be wrapped in a try/except block;
        any exceptions raised here are caught by `self.handle_exc()`.
        """
        raise NotImplementedError("Should be implemented by subclasses.")

    async def handle_exc(self, e: Exception, message: HumanChatMessage):
        """
        Handles an exception raised by `self.process_message()`. A default
        implementation is provided, however chat handlers (subclasses) should
        implement this method to provide a more helpful error response.
        """
        self._default_handle_exc(e, message)

    async def _default_handle_exc(self, e: Exception, message: HumanChatMessage):
        """
        The default definition of `handle_exc()`. This is the default used when
        the `handle_exc()` excepts.
        """
        formatted_e = traceback.format_exc()
        response = (
            f"Sorry, an error occurred. Details below:\n\n```\n{formatted_e}\n```"
        )
        self.reply(response, message)

    def reply(self, response: str, human_msg: Optional[HumanChatMessage] = None):
        agent_msg = AgentChatMessage(
            id=uuid4().hex,
            time=time.time(),
            body=response,
            reply_to=human_msg.id if human_msg else "",
        )

        for handler in self._root_chat_handlers.values():
            if not handler:
                continue

            handler.broadcast_message(agent_msg)
            break

    @property
    def lm_id(self):
        """Retrieves the language model ID from the config manager."""
        lm_provider = self.config_manager.lm_provider
        lm_provider_params = self.config_manager.lm_provider_params

        if lm_provider:
            return lm_provider.id + ":" + lm_provider_params["model_id"]
        else:
            return None

    @property
    def em_id(self):
        """Retrieves the embedding model ID from the config manager."""
        em_provider = self.config_manager.em_provider
        em_provider_params = self.config_manager.em_provider_params

        if em_provider:
            return em_provider.id + ":" + em_provider_params["model_id"]
        else:
            return None

    def get_llm_chain(self):
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
            self.log.info(
                f"Switching chat language model from {curr_lm_id} to {next_lm_id}."
            )
            self.create_llm_chain(lm_provider, lm_provider_params)
        elif self.llm_params != lm_provider_params:
            self.log.info("Chat model params changed, updating the llm chain.")
            self.create_llm_chain(lm_provider, lm_provider_params)

        self.llm_params = lm_provider_params
        return self.llm_chain

    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        raise NotImplementedError("Should be implemented by subclasses")

    def parse_args(self, message):
        args = message.body.split(" ")
        try:
            args = self.parser.parse_args(args[1:])
        except (argparse.ArgumentError, SystemExit) as e:
            response = f"{self.parser.format_usage()}"
            self.reply(response, message)
            return None
        return args
