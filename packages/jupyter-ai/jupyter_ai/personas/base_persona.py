from pydantic import BaseModel
from dataclasses import asdict
from typing import Any, Dict, Optional, Set, TYPE_CHECKING
from abc import ABC, abstractmethod
from jupyter_ai.config_manager import ConfigManager
from jupyterlab_chat.ychat import YChat
from jupyterlab_chat.models import User, Message
from .persona_awareness import PersonaAwareness
from logging import Logger

# prevents a circular import
# `PersonaManager` types have to be surrounded in single quotes
if TYPE_CHECKING:
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
    name: str # e.g. "Jupyternaut"
    description: str # e.g. "..."
    avatar_path: str # e.g. /avatars/jupyternaut.svg
    system_prompt: str # e.g. "You are a language model named..."

    ################################################
    # optional fields
    ################################################
    slash_commands: Set[str] = set("*") # change this to enable/disable slash commands
    model_uid: Optional[str] = None # e.g. "ollama:deepseek-coder-v2" 
    # ^^^ set this to automatically default to a model after a fresh start, no config file


class BasePersona(ABC):
    """
    Abstract base class that defines a persona when implemented.
    """

    ychat: YChat
    manager: 'PersonaManager'
    config: ConfigManager
    log: Logger
    awareness: PersonaAwareness

    ################################################
    # constructor
    ################################################
    def __init__(self, *, ychat: YChat, manager: 'PersonaManager', config: ConfigManager, log: Logger):
        self.ychat = ychat
        self.manager = manager
        self.config = config
        self.log = log
        self.awareness = PersonaAwareness(
            ychat=self.ychat,
            log=self.log,
            user=self.as_user()
        )
        
    ################################################
    # abstract methods, required by subclasses.
    ################################################
    @property
    @abstractmethod
    def id(self) -> str:
        """
        Must return an ID for this persona. This ID must also be unique and
        identical throughout this object's lifecycle.

        We recommend the syntax `<package-name>::<persona-name>`, e.g.
        `jupyter-ai::jupyternaut`.
        """
        pass

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
