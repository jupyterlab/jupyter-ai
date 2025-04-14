from jupyterlab_chat.ychat import YChat
from jupyterlab_chat.models import Message
from .base_persona import BasePersona
from ..config_manager import ConfigManager
from typing import ClassVar, Optional, TYPE_CHECKING
from logging import Logger
from importlib_metadata import entry_points
from .base_persona import BasePersona

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

class PersonaManager:
    """
    Class that manages all personas for a single chat.
    """

    # instance attrs
    ychat: YChat
    config_manager: ConfigManager
    event_loop: 'AbstractEventLoop'
    log: Logger
    _personas: dict[str, BasePersona]

    # class attrs
    _persona_classes: ClassVar[Optional[list[type[BasePersona]]]] = None

    def __init__(self, ychat: YChat, config_manager: ConfigManager, event_loop: 'AbstractEventLoop', log: Logger):
        self.ychat = ychat
        self.config_manager = config_manager
        self.event_loop = event_loop
        self.log = log

        self.log.info("Initializing PersonaManager...")
        if not isinstance(PersonaManager._persona_classes, list):
            self._init_persona_classes()
            assert isinstance(PersonaManager._persona_classes, list)
        
        if len(PersonaManager._persona_classes) == 0:
            self.log.warning("PersonaManager has no available personas. Please contact your server administrator.")

        self._personas = self._init_personas()
        self.log.info("Finished initializing PersonaManager.")
    
    def _init_persona_classes(self) -> None:
        """
        Initializes the list of persona *classes* by retrieving the
        `jupyter-ai.personas` entry points group.

        This list is cached in the `PersonaManager._persona_classes` class
        attribute, i.e. this method should only run once in the extension
        lifecycle.
        """
        if PersonaManager._persona_classes:
            return

        persona_eps = entry_points().select(group="jupyter_ai.personas")
        self.log.info(f"Found {len(persona_eps)} persona entry points. Loading entry points...")
        persona_classes: list[type[BasePersona]] = []

        for persona_ep in persona_eps:
            try:
                persona_class = persona_ep.load()
                assert issubclass(persona_class, BasePersona)
                persona_classes.append(persona_class)
                self.log.info(f"Loaded persona class from entry point `{persona_ep.name}`.")
            except Exception as e:
                self.log.error(
                    f"Unable to load persona from entry point `{persona_ep.name}` due to an exception printed below."
                )
                self.log.exception(e)
                continue
        
        PersonaManager._persona_classes = persona_classes
        self.log.info("Finished loading persona entry points.")
        
    def _init_personas(self) -> dict[str, BasePersona]:
        """
        Initializes the list of persona instances for the YChat instance passed
        to the constructor.
        """
        if hasattr(self, '_personas'):
            return

        persona_classes = PersonaManager._persona_classes
        assert isinstance(persona_classes, list)
        
        personas: dict[str, BasePersona] = {}
        for Persona in persona_classes:
            persona = Persona(
                ychat=self.ychat,
                manager=self,
                config=self.config_manager,
                log=self.log,
            )
            personas[persona.id] = persona

        return personas
    
    @property
    def personas(self) -> dict[str, BasePersona]:
        return self._personas

    def get_mentioned_personas(self, new_message: Message) -> list[BasePersona]:
        mentioned_ids = set(new_message.mentions)
        persona_list: list[BasePersona] = []

        for mentioned_id in mentioned_ids:
            if mentioned_id in self.personas:
                persona_list.append(self.personas[mentioned_id])
        
        return persona_list

    def route_message(self, new_message: Message):
        """
        Method that routes an incoming message to the correct persona by calling
        its `process_message()` method.

        - (TODO) If the chat contains only one persona & one user, then this
        method routes all new messages to that persona.

        - Otherwise, this method only routes new messages to personas that are
        `@`-mentioned in the message.
        """
        mentioned_personas = self.get_mentioned_personas(new_message)
        for persona in mentioned_personas:
            self.event_loop.create_task(
                persona.process_message(new_message)
            )
