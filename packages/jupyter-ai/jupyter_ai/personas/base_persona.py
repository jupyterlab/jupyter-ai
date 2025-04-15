from abc import ABC, abstractmethod
from dataclasses import asdict
from logging import Logger
from time import time
from typing import TYPE_CHECKING, Any, Dict, Optional, Set

from jupyter_ai.config_manager import ConfigManager
from jupyterlab_chat.models import Message, NewMessage, User
from jupyterlab_chat.ychat import YChat
from pydantic import BaseModel

from .persona_awareness import PersonaAwareness

# prevents a circular import
# `PersonaManager` types have to be surrounded in single quotes
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
    slash_commands: Set[str] = set("*")  # change this to enable/disable slash commands
    model_uid: Optional[str] = None  # e.g. "ollama:deepseek-coder-v2"
    # ^^^ set this to automatically default to a model after a fresh start, no config file


class BasePersona(ABC):
    """
    Abstract base class that defines a persona when implemented.
    """

    ychat: YChat
    manager: "PersonaManager"
    config: ConfigManager
    log: Logger
    awareness: PersonaAwareness

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
        Must return a PersonaDefaults object that represents the default
        settings of this persona.
        """
        pass

    @abstractmethod
    async def process_message(self, message: Message) -> None:
        """
        Processes a new message. Access history and write/stream messages via
        `self.ychat`.
        """
        # support streaming
        # handle multiple processed messages concurrently (if model service allows it)
        pass

    ################################################
    # base class methods, available to subclasses.
    ################################################
    @property
    def id(self) -> str:
        """
        Return a unique ID for this persona, which sets its username in the
        `User` object shared with other collaborative extensions.

        - This ID is guaranteed to be identical throughout this object's
        lifecycle.

        - The ID is guaranteed to follow the format
        `jupyter-ai-personas::<package-name>::<persona-class-name>`.
            - The 'jupyter-ai-personas' prefix allows consumers to easily
            distinguish AI personas from human users.

            - For example, 'Jupyternaut' always has the ID
            `jupyter-ai-personas::jupyter-ai::JupyternautPersona`.

        - The ID must be unique, so if a package provides multiple personas,
        their class names must be unique. Renaming the persona class changes the
        ID of that persona, so you should also avoid renaming it if possible.
        """
        package_name = self.__module__.split(".")[0]
        class_name = self.__class__.__name__
        return f"jupyter-ai-personas::{package_name}::{class_name}"

    @property
    def name(self) -> str:
        return self.defaults.name

    @property
    def avatar_path(self) -> str:
        return self.defaults.avatar_path

    @property
    def system_prompt(self) -> str:
        return self.defaults.system_prompt

    def as_user(self) -> User:
        return User(
            username=self.id,
            name=self.name,
            display_name=self.name,
            avatar_url=self.avatar_path,
        )

    def as_user_dict(self) -> Dict[str, Any]:
        user = self.as_user()
        return asdict(user)

    async def forward_reply_stream(self, reply_stream: "AsyncIterator"):
        """
        Forwards an async iterator, dubbed the 'reply stream', to a new message
        by this persona in the YChat.

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
