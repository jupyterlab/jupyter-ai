import argparse
import asyncio
import contextlib
import os
import traceback
from typing import (
    TYPE_CHECKING,
    Awaitable,
    ClassVar,
    Dict,
    Literal,
    Optional,
    Type,
    Union,
    cast,
)

from dask.distributed import Client as DaskClient
from jupyter_ai.callback_handlers import MetadataCallbackHandler
from jupyter_ai.config_manager import ConfigManager, Logger
from jupyter_ai.constants import BOT
from jupyter_ai_magics.providers import BaseProvider
from jupyterlab_chat.models import Message, NewMessage, User
from jupyterlab_chat.ychat import YChat
from langchain.pydantic_v1 import BaseModel
from langchain_core.messages import AIMessageChunk
from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables.config import merge_configs as merge_runnable_configs
from langchain_core.runnables.utils import Input

from .utils.streaming import ReplyStream

if TYPE_CHECKING:
    from jupyter_ai.context_providers import BaseCommandContextProvider
    from langchain_core.chat_history import BaseChatMessageHistory


def get_preferred_dir(root_dir: str, preferred_dir: Optional[str]) -> Optional[str]:
    if preferred_dir is not None and preferred_dir != "":
        preferred_dir = os.path.expanduser(preferred_dir)
        if not preferred_dir.startswith(root_dir):
            preferred_dir = os.path.join(root_dir, preferred_dir)
        return os.path.abspath(preferred_dir)
    return None


# Chat handler type, with specific attributes for each
class HandlerRoutingType(BaseModel):
    routing_method: ClassVar[Union[Literal["slash_command"]]]
    """The routing method that sends commands to this handler."""


class SlashCommandRoutingType(HandlerRoutingType):
    routing_method = "slash_command"

    slash_id: Optional[str]
    """Slash ID for routing a chat command to this handler. Only one handler
    may declare a particular slash ID. Must contain only alphanumerics and
    underscores."""


class MarkdownHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _get_help_string(self, action):
        # do not show "(default: False)" for flags as this is assumed
        if action.const is True:
            return action.help
        return super()._get_help_string(action)

    def _format_action_invocation(self, action):
        if not action.option_strings:
            return super()._format_action_invocation(action)
        else:
            action_string = super()._format_action_invocation(action)
            return f"`{action_string}`:"

    def _format_action(self, action):
        return "- " + super()._format_action(action)


class BaseChatHandler:
    """Base ChatHandler class containing shared methods and attributes used by
    multiple chat handler classes."""

    # Class attributes
    id: ClassVar[str]
    """ID for this chat handler; should be unique"""

    name: ClassVar[str]
    """User-facing name of this handler"""

    help: ClassVar[str]
    """What this chat handler does, which third-party models it contacts,
    the data it returns to the user, and so on, for display in the UI."""

    routing_type: ClassVar[HandlerRoutingType]

    uses_llm: ClassVar[bool] = True
    """Class attribute specifying whether this chat handler uses the LLM
    specified by the config. Subclasses should define this. Should be set to
    `False` for handlers like `/help`."""

    supports_help: ClassVar[bool] = True
    """Class attribute specifying whether this chat handler should
    parse the arguments and display help when user queries with
    `-h` or `--help`"""

    _requests_count: ClassVar[int] = 0
    """Class attribute set to the number of requests that Jupyternaut is
    currently handling."""

    # Instance attributes
    help_message_template: str
    """Format string template that is used to build the help message. Specified
    from traitlets configuration."""

    chat_handlers: Dict[str, "BaseChatHandler"]
    """Dictionary of chat handlers. Allows one chat handler to reference other
    chat handlers, which is necessary for some use-cases like printing the help
    message."""

    context_providers: Dict[str, "BaseCommandContextProvider"]
    """Dictionary of context providers. Allows chat handlers to reference
    context providers, which can be used to provide context to the LLM."""

    message_interrupted: Dict[str, asyncio.Event]
    """Dictionary mapping an agent message identifier to an asyncio Event
    which indicates if the message generation/streaming was interrupted."""

    def __init__(
        self,
        log: Logger,
        config_manager: ConfigManager,
        model_parameters: Dict[str, Dict],
        llm_chat_memory: "BaseChatMessageHistory",
        root_dir: str,
        preferred_dir: Optional[str],
        dask_client_future: Awaitable[DaskClient],
        help_message_template: str,
        chat_handlers: Dict[str, "BaseChatHandler"],
        context_providers: Dict[str, "BaseCommandContextProvider"],
        message_interrupted: Dict[str, asyncio.Event],
        ychat: YChat,
    ):
        self.log = log
        self.config_manager = config_manager
        self.model_parameters = model_parameters
        self.llm_chat_memory = llm_chat_memory
        self.parser = argparse.ArgumentParser(
            add_help=False, description=self.help, formatter_class=MarkdownHelpFormatter
        )
        # the default help would exit; instead implement a custom help
        if self.__class__.supports_help:
            self.parser.add_argument(
                "-h", "--help", action="store_true", help="Show this help message"
            )
        self.root_dir = os.path.abspath(os.path.expanduser(root_dir))
        self.preferred_dir = get_preferred_dir(self.root_dir, preferred_dir)
        self.dask_client_future = dask_client_future
        self.help_message_template = help_message_template
        self.chat_handlers = chat_handlers
        self.context_providers = context_providers
        self.message_interrupted = message_interrupted
        self.ychat = ychat

        self.llm: Optional[BaseProvider] = None
        self.llm_params: Optional[dict] = None
        self.llm_chain: Optional[Runnable] = None

    async def on_message(self, message: Message):
        """
        Method which receives a human message, calls `self.get_llm_chain()`, and
        processes the message via `self.process_message()`, calling
        `self.handle_exc()` when an exception is raised.

        This is the method called directly in response to new chat messages.
        """
        ChatModelProvider = self.config_manager.lm_provider

        # first, ensure a chat model is configured
        if not ChatModelProvider:
            # TODO: update this message to be more useful once we improve
            # ease-of-access to the Jupyter AI settings.
            self.reply(
                "To use Jupyter AI, please select a chat model first in the Jupyter AI settings."
            )
            return

        # ensure the current slash command is supported
        if self.routing_type.routing_method == "slash_command":
            routing_type = cast(SlashCommandRoutingType, self.routing_type)
            slash_command = "/" + routing_type.slash_id if routing_type.slash_id else ""
            if slash_command in ChatModelProvider.unsupported_slash_commands:
                self.reply(
                    "Sorry, the selected language model does not support this slash command.",
                )
                return

        # check whether the configured LLM can support a request at this time.
        if self.uses_llm and BaseChatHandler._requests_count > 0:
            chat_model_args = self.config_manager.lm_provider_params
            chat_model = ChatModelProvider(**chat_model_args)

            if not chat_model.allows_concurrency:
                self.reply(
                    "The currently selected language model can process only one request at a time. Please wait for me to reply before sending another question.",
                    message,
                )
                return

        BaseChatHandler._requests_count += 1

        if self.__class__.supports_help:
            args = self.parse_args(message, silent=True)
            if args and args.help:
                self.reply(self.parser.format_help(), message)
                return

        try:
            await self.process_message(message)
        except Exception as e:
            try:
                # we try/except `handle_exc()` in case it was overriden and
                # raises an exception by accident.
                await self.handle_exc(e, message)
            except Exception as e:
                await self._default_handle_exc(e, message)
        finally:
            BaseChatHandler._requests_count -= 1

    async def process_message(self, _human_message: Message):
        """
        Processes a human message routed to this chat handler. Chat handlers
        (subclasses) must implement this method. Don't forget to call
        `self.reply(<response>, chat, message)` at the end!

        The method definition does not need to be wrapped in a try/except block;
        any exceptions raised here are caught by `self.handle_exc()`.
        """
        raise NotImplementedError("Should be implemented by subclasses.")

    async def handle_exc(self, e: Exception, _human_message: Message):
        """
        Handles an exception raised by `self.process_message()`. A default
        implementation is provided, however chat handlers (subclasses) should
        implement this method to provide a more helpful error response.
        """
        await self._default_handle_exc(e, _human_message)

    async def _default_handle_exc(self, e: Exception, _human_message: Message):
        """
        The default definition of `handle_exc()`. This is the default used when
        the `handle_exc()` excepts.
        """
        self.log.error(e)
        lm_provider = self.config_manager.lm_provider
        if lm_provider and lm_provider.is_api_key_exc(e):
            provider_name = getattr(self.config_manager.lm_provider, "name", "")
            response = f"Oops! There's a problem connecting to {provider_name}. Please update your {provider_name} API key in the chat settings."
            self.reply(response, _human_message)
            return
        formatted_e = traceback.format_exc()
        response = (
            f"Sorry, an error occurred. Details below:\n\n```\n{formatted_e}\n```"
        )
        self.reply(response, _human_message)

    def reply(self, body: str, _human_message=None) -> str:
        """
        Adds a message to the YChat shared document that this chat handler is
        assigned to. Returns the new message ID.

        TODO: Either properly store & use reply state in YChat, or remove the
        `human_message` argument here.
        """
        bot = self.ychat.get_user(BOT["username"])
        if not bot:
            self.ychat.set_user(User(**BOT))

        id = self.ychat.add_message(NewMessage(body=body, sender=BOT["username"]))
        return id

    @property
    def persona(self):
        return self.config_manager.persona

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

    def get_model_parameters(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        return self.model_parameters.get(
            f"{provider.id}:{provider_params['model_id']}", {}
        )

    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        raise NotImplementedError("Should be implemented by subclasses")

    def parse_args(self, message: Message, silent=False):
        args = message.body.split(" ")[1:]
        try:
            arg_namespace = self.parser.parse_args(args)
        except (argparse.ArgumentError, SystemExit) as e:
            if not silent:
                response = f"{self.parser.format_usage()}"
                self.reply(response, message)
            return None
        return arg_namespace

    def get_llm_chat_memory(self) -> "BaseChatMessageHistory":
        return self.llm_chat_memory

    @property
    def output_dir(self) -> str:
        # preferred dir is preferred, but if it is not specified,
        # or if user removed it after startup, fallback to root.
        if self.preferred_dir and os.path.exists(self.preferred_dir):
            return self.preferred_dir
        else:
            return self.root_dir

    def send_help_message(self, _human_message: Optional[Message] = None) -> None:
        """Sends a help message to all connected clients."""
        lm_provider = self.config_manager.lm_provider
        unsupported_slash_commands = (
            lm_provider.unsupported_slash_commands if lm_provider else set()
        )
        chat_handlers = self.chat_handlers
        slash_commands = {k: v for k, v in chat_handlers.items() if k != "default"}
        for key in unsupported_slash_commands:
            del slash_commands[key]

        # markdown string that lists the slash commands
        slash_commands_list = "\n".join(
            [
                f"* `{command_name}` — {handler.help}"
                for command_name, handler in slash_commands.items()
            ]
        )

        context_commands_list = "\n".join(
            [
                f"* `{cp.command_id}` — {cp.help}"
                for cp in self.context_providers.values()
            ]
        )

        help_message_body = self.help_message_template.format(
            persona_name=self.persona.name,
            slash_commands_list=slash_commands_list,
            context_commands_list=context_commands_list,
        )

        self.reply(help_message_body, None)

    @contextlib.contextmanager
    def start_reply_stream(self):
        """
        Context manager which initializes a `ReplyStream`, opens it, and then
        yields the `ReplyStream`. Under this context, developers should call
        `reply_stream.write()` on the yielded reply stream to send new string
        chunks to the chat.

        Once the context is closed, the `ReplyStream` is closed automatically.
        """
        # initialize and open reply stream
        reply_stream = ReplyStream(ychat=self.ychat)
        reply_stream.open()
        # wrap the yield call in try/finally to ensure streams are closed on
        # exceptions.
        try:
            yield reply_stream
        finally:
            # close the `ReplyStream` on exit.
            reply_stream.close()

    async def stream_reply(
        self,
        input: Input,
        _human_message: Optional[Message] = None,
        pending_msg="Generating response",
        config: Optional[RunnableConfig] = None,
    ):
        """
        Streams a reply to a human message by invoking
        `self.llm_chain.astream()`. A LangChain `Runnable` instance must be
        bound to `self.llm_chain` before invoking this method.

        Arguments
        ---------
        - `input`: The input to your runnable. The type of `input` depends on
        the runnable in `self.llm_chain`, but is usually a dictionary whose keys
        refer to input variables in your prompt template.

        - `_human_message`: The human message being replied to. Currently
        unused. TODO: Either re-implement this for v3 or remove it.

         - `_pending_msg` (optional): Changes the default pending message from
        "Generating response". Not supported at this time. TODO: Re-implement
        this for v3.

        - `config` (optional): A `RunnableConfig` object that specifies
        additional configuration when streaming from the runnable.

         - `pending_msg` (optional): Changes the default pending message from
        "Generating response".
        """
        assert self.llm_chain
        assert isinstance(self.llm_chain, Runnable)

        received_first_chunk = False
        metadata_handler = MetadataCallbackHandler()
        base_config: RunnableConfig = {
            "callbacks": [metadata_handler],
        }
        merged_config: RunnableConfig = merge_runnable_configs(base_config, config)

        # start with a pending message
        with self.start_reply_stream() as reply_stream:
            # stream response in chunks. this works even if a provider does not
            # implement streaming, as `astream()` defaults to yielding `_call()`
            # when `_stream()` is not implemented on the LLM class.
            chunk_generator = self.llm_chain.astream(input, config=merged_config)
            # TODO v3: re-implement stream interrupt
            stream_interrupted = False
            async for chunk in chunk_generator:
                if isinstance(chunk, AIMessageChunk) and isinstance(chunk.content, str):
                    reply_stream.write(chunk.content)
                elif isinstance(chunk, str):
                    reply_stream.write(chunk)
                else:
                    self.log.error(f"Unrecognized type of chunk yielded: {type(chunk)}")
                    break

            # if stream was interrupted, add a tombstone
            if stream_interrupted:
                stream_tombstone = "\n\n(AI response stopped by user)"
                reply_stream.write(stream_tombstone)


class GenerationInterrupted(asyncio.CancelledError):
    """Exception raised when streaming is cancelled by the user"""
