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

# EPG := entry point group
EPG_NAME = "jupyter_ai.personas"
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

        if not isinstance(PersonaManager._persona_classes, list):
            self._init_persona_classes()
            assert isinstance(PersonaManager._persona_classes, list)

        self._personas = self._init_personas()
    
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

        persona_eps = entry_points().select(group=EPG_NAME)
        self.log.info(f"Found {len(persona_eps)} entry points under '{EPG_NAME}'.")
        self.log.info("PENDING: Loading AI persona classes from entry points...")
        persona_classes: list[type[BasePersona]] = []

        for persona_ep in persona_eps:
            try:
                persona_class = persona_ep.load()
                assert issubclass(persona_class, BasePersona)
                persona_classes.append(persona_class)
                class_module, class_name = persona_ep.value.split(":")
                self.log.info(f"  - Loaded AI persona class '{class_name}' from '{class_module}' using entry point '{persona_ep.name}'.")
            except Exception as e:
                self.log.error(
                    f"  - Unable to load AI persona from entry point `{persona_ep.name}` due to an exception printed below."
                )
                self.log.exception(e)
                continue
        
        if len(persona_classes) > 0:
            self.log.info(f"SUCCESS: Loaded {len(persona_classes)} AI persona classes from entry points.")
        else:
            self.log.error(
                "ERROR: Jupyter AI has no AI personas available. "
                + "Please verify your server configuration and open a new issue on our GitHub repo if this warning persists."
            )
        PersonaManager._persona_classes = persona_classes
        
    def _init_personas(self) -> dict[str, BasePersona]:
        """
        Initializes the list of persona instances for the YChat instance passed
        to the constructor.
        """
        if hasattr(self, '_personas') or len(PersonaManager._persona_classes) == 0:
            return

        self.log.info(f"PENDING: Initializing AI personas for chat room '{self.ychat.get_id()}'...")
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
            if persona.id in personas:
                class_name = persona.__class__.__name__
                self.log.warning(
                    f"  - WARNING: Skipping persona '{persona.name}' from '{persona.__module__}' because another persona has an identical ID '{persona.id}'. "
                    + f"Personas must all have unique IDs. Please rename the persona class from '{class_name}' to something unique to dismiss this warning."
                )
                continue
            else:
                self.log.info(f"  - Initialized persona '{persona.name}' (ID: '{persona.id}').")
                personas[persona.id] = persona

        self.log.info(f"SUCCESS: Initialized {len(personas)} AI personas for chat room '{self.ychat.get_id()}'.")
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
        if not len(mentioned_personas):
            return

        mentioned_persona_names = [persona.name for persona in mentioned_personas]
        self.log.info(f"Received new user message mentioning the following personas: {mentioned_persona_names}.")
        for persona in mentioned_personas:
            self.event_loop.create_task(
                persona.process_message(new_message)
            )
