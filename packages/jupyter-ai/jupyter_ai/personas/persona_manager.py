from jupyterlab_chat.ychat import YChat
from jupyterlab_chat.models import Message
from .base_persona import BasePersona
from ..config_manager import ConfigManager
from typing import ClassVar, List, Optional, Set, Type
from logging import Logger
from importlib_metadata import entry_points

class PersonaManager:
    """
    Class that manages all personas for a single chat.
    """

    # instance attrs
    ychat: YChat
    log: Logger
    _personas: List[BasePersona]
    _persona_ids: Set[str]

    # class attrs
    _persona_classes: ClassVar[Optional[List[Type[BasePersona]]]] = None

    def __init__(self, ychat: YChat, config_manager: ConfigManager, log: Logger):
        self.log = log
        self.ychat = ychat
        self.config_manager = config_manager

        self.log.info("Initializing PersonaManager...")
        if not isinstance(PersonaManager._persona_classes, list):
            self._init_persona_classes()
        
        if len(PersonaManager._persona_classes) == 0:
            self.log.warning("PersonaManager has no available personas. Please contact your server administrator.")

        self._personas = self._init_personas()
        self._persona_ids = set([persona.id for persona in self._personas])
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
        persona_classes: List[Type[BasePersona]] = []

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
        
    def _init_personas(self) -> List[BasePersona]:
        """
        Initializes the list of persona instances for the YChat instance passed
        to the constructor.
        """
        if hasattr(self, '_personas'):
            return

        persona_classes = PersonaManager._persona_classes
        assert isinstance(persona_classes, list)
        
        personas: List[BasePersona] = []
        for Persona in persona_classes:
            persona = Persona(ychat=self.ychat, config_manager=self.config_manager)
            personas.append(persona)

        return personas
    
    @property
    def personas(self) -> List[BasePersona]:
        return self._personas

    @property
    def persona_ids(self) -> Set[str]:
        return self._persona_ids

    async def route_message(self, message: Message):
        """
        Method that routes an incoming message to the correct persona by calling
        its `process_message()` method.

        - If the chat contains only one persona & one user, then this method
        routes all new messages to that persona.

        - Otherwise, this method only routes new messages to personas that are
        `@`-mentioned in the message.
        """
        # TODO. Just routing everything to everybody now.

        if message.sender in self.persona_ids:
            return
        
        for persona in self.personas:
            pass
