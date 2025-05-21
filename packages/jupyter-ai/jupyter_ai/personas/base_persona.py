from abc import ABC, abstractmethod
from dataclasses import asdict
from logging import Logger
from time import time
from typing import TYPE_CHECKING, Any, Optional

from jupyter_ai.config_manager import ConfigManager
from jupyterlab_chat.models import Message, NewMessage, User
from jupyterlab_chat.ychat import YChat
from pydantic import BaseModel

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


class BasePersona(ABC):
    """
    Abstract base class that defines a persona when implemented.
    """

    ychat: YChat
    """
    Reference to the `YChat` that this persona instance is scoped to.
    Automatically set by `BasePersona`.
    """

    manager: "PersonaManager"
    """
    Reference to the `PersonaManager` for this `YChat`, which manages this
    instance. Automatically set by `BasePersona`.
    """

    config: ConfigManager
    """
    Reference to the `ConfigManager` singleton, which is used to read & write from
    the Jupyter AI settings. Automatically set by `BasePersona`.
    """

    log: Logger
    """
    The logger for this instance. Automatically set by `BasePersona`.
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

    ################################################
    # constructor
    ################################################
    def __init__(
        self,
        *,
        ychat: YChat,
        manager: "PersonaManager",
        config: ConfigManager,
        log: Logger,
    ):
        self.ychat = ychat
        self.manager = manager
        self.config = config
        self.log = log
        self.awareness = PersonaAwareness(
            ychat=self.ychat, log=self.log, user=self.as_user()
        )

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

        try:
            self.awareness.set_local_state_field("isWriting", True)
            async for chunk in reply_stream:
                if not stream_id:
                    stream_id = self.ychat.add_message(
                        NewMessage(body="", sender=self.id)
                    )

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

    def send_message(self, body: str) -> None:
        """
        Sends a new message to the chat from this persona.
        """
        self.ychat.add_message(NewMessage(body=body, sender=self.id))
