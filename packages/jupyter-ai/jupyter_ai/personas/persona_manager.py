from __future__ import annotations

import asyncio
import importlib.util
import inspect
import os
from glob import glob
from logging import Logger
from pathlib import Path
from time import time_ns
from typing import TYPE_CHECKING, Any, ClassVar

from importlib_metadata import entry_points
from jupyterlab_chat.models import Message
from jupyterlab_chat.ychat import YChat
from traitlets.config import LoggingConfigurable

from ..config_manager import ConfigManager
from ..mcp.mcp_config_loader import MCPConfigLoader
from .base_persona import BasePersona
from .directories import find_dot_dir, find_workspace_dir

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

    from jupyter_server_fileid.manager import (  # type: ignore[import-untyped]
        BaseFileIdManager,
    )

# EPG := entry point group
EPG_NAME = "jupyter_ai.personas"


class PersonaManager(LoggingConfigurable):
    """
    Class that manages all personas for a single chat.
    """

    # instance attrs
    ychat: YChat
    config_manager: ConfigManager
    fileid_manager: BaseFileIdManager
    root_dir: str
    event_loop: AbstractEventLoop
    _mcp_config_loader: MCPConfigLoader

    log: Logger  # type: ignore
    """
    The `logging.Logger` instance used by this class. This is automatically set
    by the `LoggingConfigurable` parent class; this declaration only hints the
    type for type checkers.
    """

    _persona_classes: ClassVar[list[type[BasePersona]] | None] = None
    _personas: dict[str, BasePersona]
    file_id: str


    def __init__(
        self,
        *args,
        room_id: str,
        ychat: YChat,
        config_manager: ConfigManager,
        fileid_manager: BaseFileIdManager,
        root_dir: str,
        event_loop: AbstractEventLoop,
        message_interrupted: dict[str, asyncio.Event],
        **kwargs,
    ):
        # Forward other arguments to parent class
        super().__init__(*args, **kwargs)

        # Bind instance attributes
        self.room_id = room_id
        self.ychat = ychat
        self.config_manager = config_manager
        self.fileid_manager = fileid_manager
        self.root_dir = root_dir
        self.event_loop = event_loop
        self.message_interrupted = message_interrupted

        # Store file ID
        self.file_id = room_id.split(":")[2]

        # Initialize MCP config loader
        self._mcp_config_loader = MCPConfigLoader()

        # Load persona classes from entry points.
        # This is stored in a class attribute (global to all instances) because
        # the entry points are immutable after the server starts, so they only
        # need to be loaded once.
        if not isinstance(self._persona_classes, list):
            self._init_persona_classes()
            assert isinstance(self._persona_classes, list)

        self._personas = self._init_personas()

    def _init_persona_classes(self) -> None:
        """
        Initializes the list of persona *classes* by retrieving the
        `jupyter-ai.personas` entry points group.

        # TODO: fix this part of docs now that we have it as an instance attr.
        This list is cached in the `self._persona_classes` instance
        attribute, .e. this method should only run once in the extension
        lifecycle.
        """
        # Loading is in two parts:
        # 1. Load persona classes from package entry points.
        # 2. Load persona classes from local filesystem.
        #
        # This allows for lightweight development of new personas by the user in
        # their local filesystem. The first part is done here, and the second
        # part is done in `_init_personas()`.

        persona_eps = entry_points().select(group=EPG_NAME)
        self.log.info(f"Found {len(persona_eps)} entry points under '{EPG_NAME}'.")
        self.log.info("PENDING: Loading AI persona classes from entry points...")
        start_time_ns = time_ns()
        persona_classes: list[type[BasePersona]] = []

        for persona_ep in persona_eps:
            try:
                # Load a persona class from each entry point
                persona_class = persona_ep.load()
                assert issubclass(persona_class, BasePersona)
                persona_classes.append(persona_class)
                class_module, class_name = persona_ep.value.split(":")
                self.log.info(
                    f"  - Loaded AI persona class '{class_name}' from '{class_module}' using entry point '{persona_ep.name}'."
                )
            except Exception:
                # On exception, log an error and continue.
                # This does not stop the surrounding `for` loop. If a persona
                # fails to load, it should not halt other personas from loading.
                self.log.exception(
                    f"  - Unable to load AI persona from entry point `{persona_ep.name}` due to an exception printed below."
                )
                continue

        if len(persona_classes) > 0:
            elapsed_time_ms = (time_ns() - start_time_ns) // 1000
            self.log.info(
                f"SUCCESS: Loaded {len(persona_classes)} AI persona classes from entry points. Time elapsed: {elapsed_time_ms}ms."
            )
        else:
            self.log.error(
                "ERROR: Jupyter AI has no AI personas available. "
                + "Please verify your server configuration and open a new issue on our GitHub repo if this warning persists."
            )

        # Load persona classes from local filesystem
        persona_classes.extend(load_from_dir(self.get_dotjupyter_dir(), self.log))

        self._persona_classes = persona_classes

    def _init_personas(self) -> dict[str, BasePersona]:
        """
        Initializes the list of persona instances for the YChat instance passed
        to the constructor.
        """
        # Ensure that persona classes were initialized first
        persona_classes = self._persona_classes
        assert isinstance(persona_classes, list)

        # If no persona classes are available, log a warning and return
        if len(persona_classes) == 0:
            self.log.warning("No AI personas are available.")
            return {}

        self.log.info(
            f"PENDING: Initializing AI personas for chat room '{self.ychat.get_id()}'..."
        )
        start_time_ns = time_ns()

        personas: dict[str, BasePersona] = {}
        for Persona in persona_classes:
            try:
                persona = Persona(
                    parent=self,
                    ychat=self.ychat,
                    config_manager=self.config_manager,
                    message_interrupted=self.message_interrupted,
                )
            except Exception:
                self.log.exception(
                    f"The persona provided by `{Persona.__module__}` "
                    "raised an exception while initializing, "
                    "printed below."
                )
                continue

            if persona.id in personas:
                class_name = persona.__class__.__name__
                self.log.warning(
                    f"  - WARNING: Skipping persona '{persona.name}' from '{persona.__module__}' because another persona has an identical ID '{persona.id}'. "
                    + f"Personas must all have unique IDs. Please rename the persona class from '{class_name}' to something unique to dismiss this warning."
                )
                continue

            self.log.info(
                f"  - Initialized persona '{persona.name}' (ID: '{persona.id}')."
            )
            personas[persona.id] = persona

        elapsed_time_ms = (time_ns() - start_time_ns) // 1_000_000
        self.log.info(
            f"SUCCESS: Initialized {len(personas)} AI personas for chat room '{self.ychat.get_id()}'. Time elapsed: {elapsed_time_ms}ms."
        )
        return personas

    @property
    def personas(self) -> dict[str, BasePersona]:
        """
        Returns a dictionary of all available persona instances, keyed by
        persona ID.
        """
        return self._personas

    def get_mentioned_personas(self, new_message: Message) -> list[BasePersona]:
        """
        Returns a list of all personas `@`-mentioned in a chat message, given a
        reference to the chat message.
        """
        mentioned_ids = set(new_message.mentions or [])
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
        self.log.info(
            f"Received new user message mentioning the following personas: {mentioned_persona_names}."
        )
        for persona in mentioned_personas:
            self.event_loop.create_task(persona.process_message(new_message))

    def get_chat_path(self, relative: bool = False) -> str:
        """
        Returns the absolute path of the chat file assigned to this
        `PersonaManager`.

        To get a path relative to the `ContentsManager` root directory, call
        this method with `relative=True`.
        """
        relpath = self.fileid_manager.get_path(self.file_id)
        if not relpath:
            raise Exception(f"Unable to locate chat with file ID: '{self.file_id}'.")
        if relative:
            return relpath

        abspath = os.path.join(self.root_dir, relpath)
        return abspath

    def get_chat_dir(self) -> str:
        """
        Returns the absolute path of the parent directory of the chat file
        assigned to this `PersonaManager`.
        """
        abspath = self.get_chat_path()
        return os.path.dirname(abspath)

    def get_dotjupyter_dir(self) -> str | None:
        """
        Returns the path to the .jupyter directory for the current chat.
        """
        return find_dot_dir(self.get_chat_dir(), ".jupyter", root_dir=self.root_dir)

    def get_workspace_dir(self) -> str:
        """
        Returns the path to the workspace directory for the current chat.
        """
        return find_workspace_dir(self.get_chat_dir(), root_dir=self.root_dir)

    def get_mcp_config(self) -> dict[str, Any]:
        """
        Returns the MCP config for the current chat.
        """
        jdir = self.get_dotjupyter_dir()
        if jdir is None:
            return {}
        else:
            return self._mcp_config_loader.get_config(jdir)


def load_from_dir(root_dir: str, log: Logger) -> list[type[BasePersona]]:
    """
    Load _persona class declarations_ from Python files in the local filesystem.

    Those class declarations are then used to instantiate personas by the
    `PersonaManager`.

    Scans the root_dir for .py files containing `persona` in their name that do
    _not_ start with a single `_` (i.e. private modules are skipped). Then, it 
    dynamically imports them, and extracts any class declarations that are
    subclasses of `BasePersona`.

         Args:
         root_dir: Directory to scan for persona Python files.
         log: Logger instance for logging messages.

     Returns:
         List of `BasePersona` subclasses found in the directory.
    """
    persona_classes: list[type[BasePersona]] = []

    # Check if root directory exists
    if not os.path.exists(root_dir):
        return persona_classes

    # Find all .py files in the root directory that contain "persona" in the name
    try:
        all_py_files = glob(os.path.join(root_dir, "*.py"))
        py_files = [f for f in all_py_files if "persona" in Path(f).stem.lower()]
    except Exception as e:
        # On exception with glob operation, return empty list
        log.debug(f"{type(e).__name__} occurred while searching for Python files in {root_dir}")
        return persona_classes

    if py_files:
        log.info(f"Loading persona files from {root_dir}: {[Path(f).name for f in py_files]}")
    
    # For each .py file, dynamically import the module and extract all
    # BasePersona subclasses.
    for py_file in py_files:
        try:
            # Get module name from file path
            module_name = Path(py_file).stem

            # Skip if module name starts with underscore (private modules)
            if module_name.startswith("_"):
                continue

            # Create module spec and load the module
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec is None or spec.loader is None:
                continue

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find all classes in the module that are BasePersona subclasses
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Check if it's a subclass of BasePersona but not BasePersona itself
                if (
                    issubclass(obj, BasePersona)
                    and obj is not BasePersona
                    and obj.__module__ == module_name
                ):
                    persona_classes.append(obj)

        except Exception as e:
            # On exception, log error and continue to next file
            # This mirrors the error handling pattern from entry point loading
            log.error(f"Unable to load persona classes from '{py_file}'")
            log.error(f"Error was: {type(e).__name__}: {e} - Unable to load persona classes from '{py_file}'")
            continue

    return persona_classes
