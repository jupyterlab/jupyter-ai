from pydantic import BaseModel
from typing import Optional, Set
from abc import ABC, abstractmethod
from jupyter_ai.config_manager import ConfigManager
from jupyterlab_chat.ychat import YChat
from jupyterlab_chat.models import User

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

    ################################################
    # constructor
    ################################################
    def __init__(self, *args, config_manager: ConfigManager, ychat: YChat, **kwargs):
        self.ychat = ychat
        self.config = config_manager
        super().__init__(*args, **kwargs)

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
    
    def as_chat_user(self) -> User:
        return User(
            username=self.id,
            name=self.name,
            display_name=self.name,
            avatar_url=self.avatar_path,
        )
    
    
    