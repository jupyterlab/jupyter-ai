import asyncio
from abc import ABC, ABCMeta, abstractmethod
from dataclasses import asdict
from logging import Logger
from time import time
from typing import TYPE_CHECKING, Any, Optional

from jupyter_ai.config_manager import ConfigManager
from jupyterlab_chat.models import Message, NewMessage, User
from jupyterlab_chat.ychat import YChat
from pydantic import BaseModel
from traitlets import MetaHasTraits
from traitlets.config import LoggingConfigurable

from .persona_awareness import PersonaAwareness

# prevents a circular import
# types imported under this block have to be surrounded in single quotes on use
if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from .persona_manager import PersonaManager


class PersonaDefaults(BaseModel):
    """
    Data structure that represents the default settings of a persona. Each persona
    must define some basic default settings, like its name.

    Each of these settings can be overwritten through the settings UI.
    """

    ################################################
    # required fields
    ################################################
    name: str  # e.g. "Jupyternaut"
    description: str  # e.g. "..."
    avatar_path: str  # e.g. /avatars/jupyternaut.svg
    system_prompt: str  # e.g. "You are a language model named..."

    ################################################
    # optional fields
    ################################################
    slash_commands: set[str] = set("*")  # change this to enable/disable slash commands
    model_uid: Optional[str] = None  # e.g. "ollama:deepseek-coder-v2"
    # ^^^ set this to automatically default to a model after a fresh start, no config file


class ABCLoggingConfigurableMeta(ABCMeta, MetaHasTraits):
    """
    Metaclass required for `BasePersona` to inherit from both `ABC` and
    `LoggingConfigurable`. This pattern is also followed by `BaseFileIdManager`
    from `jupyter_server_fileid`.
    """


class BasePersona(ABC, LoggingConfigurable, metaclass=ABCLoggingConfigurableMeta):
    """
    Abstract base class that defines a persona when implemented.
    """

    ychat: YChat
    """
    Reference to the `YChat` that this persona instance is scoped to.
    Automatically set by `BasePersona`.
    """

    parent: "PersonaManager"  # type: ignore
    """
    Reference to the `PersonaManager` for this `YChat`, which manages this
    instance. Automatically set by the `LoggingConfigurable` parent class.
    """

    config_manager: ConfigManager
    """
    Reference to the `ConfigManager` singleton, which is used to read & write from
    the Jupyter AI settings. Automatically set by `BasePersona`.
    """

    log: Logger  # type: ignore
    """
    The `logging.Logger` instance used by this class. Automatically set by the
    `LoggingConfigurable` parent class.
    """

    awareness: PersonaAwareness
    """
    A custom wrapper around `self.ychat.awareness: pycrdt.Awareness`. The
    default `Awareness` API does not support setting local state fields on
    multiple AI personas, so any awareness method calls should be done through
    this attribute (`self.awareness`) instead of `self.ychat.awareness`. See the
    documentation in `PersonaAwareness` for more information.

    Automatically set by `BasePersona`.
    """

    message_interrupted: dict[str, asyncio.Event]
    """Dictionary mapping an agent message identifier to an asyncio Event
    which indicates if the message generation/streaming was interrupted."""

    ################################################
    # constructor
    ################################################
    def __init__(
        self,
        *args,
        ychat: YChat,
        config_manager: ConfigManager,
        message_interrupted: dict[str, asyncio.Event],
        **kwargs,
    ):
        # Forward other arguments to parent class
        super().__init__(*args, **kwargs)

        # Bind arguments to instance attributes
        self.ychat = ychat
        self.config_manager = config_manager
        self.message_interrupted = message_interrupted

        # Initialize custom awareness object for this persona
        self.awareness = PersonaAwareness(
            ychat=self.ychat, log=self.log, user=self.as_user()
        )

        # Register this persona as a user in the chat
        self.ychat.set_user(self.as_user())

    ################################################
    # abstract methods, required by subclasses.
    ################################################
    @property
    @abstractmethod
    def defaults(self) -> PersonaDefaults:
        """
        Returns a `PersonaDefaults` data model that represents the default
        settings of this persona.

        This is an abstract method that must be implemented by subclasses.
        """

    @abstractmethod
    async def process_message(self, message: Message) -> None:
        """
        Processes a new message. This method exclusively defines how new
        messages are handled by a persona, and should be considered the "main
        entry point" to this persona. Reading chat history and streaming a reply
        can be done through method calls to `self.ychat`. See
        `JupyternautPersona` for a reference implementation on how to do so.

        This is an abstract method that must be implemented by subclasses.
        """

    ################################################
    # base class methods, available to subclasses.
    ################################################
    @property
    def id(self) -> str:
        """
        Returns a static & unique ID for this persona. This sets the `username`
        field in the data model returned by `self.as_user()`.

        The ID is guaranteed to follow the format
        `jupyter-ai-personas::<package-name>::<persona-class-name>`. The prefix
        allows consumers to easily distinguish AI personas from human users.

        If a package provides multiple personas, their class names must be
        different to ensure that their IDs are unique.
        """
        package_name = self.__module__.split(".")[0]
        class_name = self.__class__.__name__
        return f"jupyter-ai-personas::{package_name}::{class_name}"

    @property
    def name(self) -> str:
        """
        Returns the name shown on messages from this persona in the chat. This
        sets the `name` and `display_name` fields in the data model returned by
        `self.as_user()`. Provided by `BasePersona`.

        NOTE/TODO: This currently just returns the value set in `self.defaults`.
        This is set here because we may require this field to be configurable
        for all personas in the future.
        """
        return self.defaults.name

    @property
    def avatar_path(self) -> str:
        """
        Returns the URL route that serves the avatar shown on messages from this
        persona in the chat. This sets the `avatar_url` field in the data model
        returned by `self.as_user()`. Provided by `BasePersona`.

        NOTE/TODO: This currently just returns the value set in `self.defaults`.
        This is set here because we may require this field to be configurable
        for all personas in the future.
        """
        return self.defaults.avatar_path

    @property
    def system_prompt(self) -> str:
        """
        Returns the system prompt used by this persona. Provided by `BasePersona`.

        NOTE/TODO: This currently just returns the value set in `self.defaults`.
        This is set here because we may require this field to be configurable
        for all personas in the future.
        """
        return self.defaults.system_prompt

    def as_user(self) -> User:
        """
        Returns the `jupyterlab_chat.models:User` model that represents this
        persona in the chat. This model also includes all attributes from
        `jupyter_server.auth:JupyterUser`, the user model returned by the
        `IdentityProvider` in Jupyter Server.

        This method is provided by `BasePersona`.
        """
        return User(
            username=self.id,
            name=self.name,
            display_name=self.name,
            avatar_url=self.avatar_path,
            bot=True,
        )

    def as_user_dict(self) -> dict[str, Any]:
        """
        Returns `self.as_user()` as a Python dictionary. This method is provided
        by `BasePersona`.
        """
        user = self.as_user()
        return asdict(user)

    async def stream_message(self, reply_stream: "AsyncIterator") -> None:
        """
        Takes an async iterator, dubbed the 'reply stream', and streams it to a
        new message by this persona in the YChat.

        - Creates a new message upon receiving the first chunk from the reply
        stream, then continuously updates it until the stream is closed.

        - Automatically manages its awareness state to show writing status.
        """
        stream_id: Optional[str] = None
        stream_interrupted = False
        try:
            self.awareness.set_local_state_field("isWriting", True)
            async for chunk in reply_stream:
                if (
                    stream_id
                    and stream_id in self.message_interrupted.keys()
                    and self.message_interrupted[stream_id].is_set()
                ):
                    try:
                        # notify the model provider that streaming was interrupted
                        # (this is essential to allow the model to stop generating)
                        await reply_stream.athrow(  # type:ignore[attr-defined]
                            GenerationInterrupted()
                        )
                    except GenerationInterrupted:
                        # do not let the exception bubble up in case if
                        # the provider did not handle it
                        pass
                    stream_interrupted = True
                    break

                if not stream_id:
                    stream_id = self.ychat.add_message(
                        NewMessage(body="", sender=self.id)
                    )
                    self.message_interrupted[stream_id] = asyncio.Event()
                    self.awareness.set_local_state_field("isWriting", stream_id)

                assert stream_id
                self.ychat.update_message(
                    Message(
                        id=stream_id,
                        body=chunk,
                        time=time(),
                        sender=self.id,
                        raw_time=False,
                    ),
                    append=True,
                )
        except Exception as e:
            self.log.error(
                f"Persona '{self.name}' encountered an exception printed below when attempting to stream output."
            )
            self.log.exception(e)
        finally:
            self.awareness.set_local_state_field("isWriting", False)
            if stream_id:
                # if stream was interrupted, add a tombstone
                if stream_interrupted:
                    stream_tombstone = "\n\n(AI response stopped by user)"
                    self.ychat.update_message(
                        Message(
                            id=stream_id,
                            body=stream_tombstone,
                            time=time(),
                            sender=self.id,
                            raw_time=False,
                        ),
                        append=True,
                    )
                if stream_id in self.message_interrupted.keys():
                    del self.message_interrupted[stream_id]

    def send_message(self, body: str) -> None:
        """
        Sends a new message to the chat from this persona.
        """
        self.ychat.add_message(NewMessage(body=body, sender=self.id))

    def get_chat_path(self, relative: bool = False) -> str:
        """
        Returns the absolute path of the chat file assigned to this persona.

        To get a path relative to the `ContentsManager` root directory, call
        this method with `relative=True`.
        """
        return self.parent.get_chat_path(relative=relative)

    def get_chat_dir(self) -> str:
        """
        Returns the absolute path to the parent directory of the chat file
        assigned to this persona.
        """
        return self.parent.get_chat_dir()

    def get_dotjupyter_dir(self) -> Optional[str]:
        """
        Returns the path to the .jupyter directory for the current chat.
        """
        return self.parent.get_dotjupyter_dir()

    def get_workspace_dir(self) -> str:
        """
        Returns the path to the workspace directory for the current chat.
        """
        return self.parent.get_workspace_dir()

    def get_mcp_config(self) -> dict[str, Any]:
        """
        Returns the MCP config for the current chat.
        """
        return self.parent.get_mcp_config()
    
    def shutdown(self) -> None:
        """
        Shuts the persona down. This method should:
         
        - Halt all background tasks started by this instance.
        - Remove the persona from the chat awareness

        This method will be called when `/refresh-personas` is run, and may be
        called when the server is shutting down or when a chat session is
        closed.

        Subclasses may need to override this method to add custom shutdown
        logic. The override should generally call `super().shutdown()` first
        before running custom shutdown logic.
        """
        # Stop awareness heartbeat task & remove self from chat awareness
        self.awareness.shutdown()


class GenerationInterrupted(asyncio.CancelledError):
    """Exception raised when streaming is cancelled by the user"""
