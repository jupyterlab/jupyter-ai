import argparse
import time
import traceback

# necessary to prevent circular import
from typing import TYPE_CHECKING, Dict, Optional, Type
from uuid import uuid4

from jupyter_ai.config_manager import ConfigManager, Logger
from jupyter_ai.models import AgentChatMessage, HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.chat_models.base import BaseChatModel

if TYPE_CHECKING:
    from jupyter_ai.handlers import RootChatHandler


class BaseChatHandler:
    """Base ChatHandler class containing shared methods and attributes used by
    multiple chat handler classes."""

    def __init__(
        self,
        log: Logger,
        config_manager: ConfigManager,
        root_chat_handlers: Dict[str, "RootChatHandler"],
    ):
        self.log = log
        self.config_manager = config_manager
        self._root_chat_handlers = root_chat_handlers
        self.parser = argparse.ArgumentParser()
        self.llm = None
        self.llm_params = None
        self.llm_chain = None

    async def process_message(self, message: HumanChatMessage):
        """Processes the message passed by the root chat handler."""
        try:
            await self._process_message(message)
        except Exception as e:
            formatted_e = traceback.format_exc()
            response = f"Sorry, something went wrong and I wasn't able to index that path.\n\n```\n{formatted_e}\n```"
            self.reply(response, message)

    async def _process_message(self, message: HumanChatMessage):
        """Processes the message passed by the `Router`"""
        raise NotImplementedError("Should be implemented by subclasses.")

    def reply(self, response, human_msg: Optional[HumanChatMessage] = None):
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
