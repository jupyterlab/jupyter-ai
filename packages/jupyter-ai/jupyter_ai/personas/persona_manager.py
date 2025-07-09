from __future__ import annotations

import asyncio
import importlib.util
import inspect
import os
import sys
import traceback
from glob import glob
from logging import Logger
from pathlib import Path
from time import time_ns
from typing import TYPE_CHECKING

from importlib_metadata import entry_points
from jupyterlab_chat.models import Message, NewMessage
from jupyterlab_chat.ychat import YChat
from traitlets.config import LoggingConfigurable
from traitlets import Unicode

from ..config_manager import ConfigManager
from ..mcp.mcp_config_loader import MCPConfigLoader
from .base_persona import BasePersona
from .directories import find_dot_dir, find_workspace_dir
from jupyterlab_chat.models import User

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from typing import Any, ClassVar

    from jupyter_server_fileid.manager import (  # type: ignore[import-untyped]
        BaseFileIdManager,
    )

# EPG := entry point group
EPG_NAME = "jupyter_ai.personas"

SYSTEM_USERNAME = "hidden::jupyter_ai_system"
"""
Username used for system messages shown to the user.
"""


class PersonaManager(LoggingConfigurable):
    """
    Class that manages all personas for a single chat.
    """

    # Configurable traits
    default_persona_id = Unicode(
        default_value="jupyter-ai-personas::jupyter_ai::JupyternautPersona",
        help="" \
        "The ID of the default persona. If configured, the default persona " \
        "will automatically reply in a single-user chats until another " \
        "persona is `@`-mentioned. " \
        "Defaults to: 'jupyter-ai-personas::jupyter_ai::JupyternautPersona'. ",
        allow_none=True,
        config=True,
    )

    # class attr storing persona classes from entry points
    # We treat this as a class attribute so that we only have to load them once
    _ep_persona_classes: ClassVar[list[dict] | None] = None

    # instance attrs
    ychat: YChat
    config_manager: ConfigManager
    fileid_manager: BaseFileIdManager
    root_dir: str
    event_loop: AbstractEventLoop
    _mcp_config_loader: MCPConfigLoader
    last_mentioned_persona: BasePersona | None

    log: Logger  # type: ignore
    """
    The `logging.Logger` instance used by this class. This is automatically set
    by the `LoggingConfigurable` parent class; this declaration only hints the
    type for type checkers.
    """

    # Local persona classes are instance attributes to support frequent reloading
    _local_persona_classes: list[dict] | None = None
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
        # Initialize last_mentioned_persona to None
        self.last_mentioned_persona = None

        self._init_persona_classes()
        self.log.info(f"Persona classes loaded in chat '{self.room_id}'.")
        self._personas = self._init_personas()
        self.log.info(f"Personas initialized in chat '{self.room_id}'.")
        if self.default_persona:
            self.log.info(f"Default persona set to '{self.default_persona.name}' in chat '{self.room_id}'.")
        else:
            self.log.warning(f"No default persona is set in chat '{self.room_id}'.")

    def _init_persona_classes(self) -> None:
        """Read entry-point and local persona classes."""
        if PersonaManager._ep_persona_classes is None:
            self._init_ep_persona_classes()
            assert isinstance(PersonaManager._ep_persona_classes, list)
        self._init_local_persona_classes()

    def _init_ep_persona_classes(self) -> None:
        """
        Initializes the list of persona *classes* by retrieving the
        `jupyter-ai.personas` entry points group.
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
        persona_classes: list[dict] = []

        for persona_ep in persona_eps:
            try:
                # Load a persona class from each entry point
                persona_class = persona_ep.load()
                assert issubclass(persona_class, BasePersona)
                persona_classes.append(
                    {
                        "module": persona_ep.name,
                        "persona_class": persona_class,
                        "traceback": None,
                    }
                )
                class_module, class_name = persona_ep.value.split(":")
                self.log.info(
                    f"  - Loaded AI persona class '{class_name}' from '{class_module}' using entry point '{persona_ep.name}'."
                )
            except Exception:
                # On exception, log an error and continue.
                # This does not stop the surrounding `for` loop. If a persona
                # fails to load, it should not halt other personas from loading.
                tb_str = traceback.format_exc()
                self.log.exception(
                    f"  - Unable to load AI persona from entry point `{persona_ep.name}` due to an exception printed below.\n{tb_str}"
                )
                persona_classes.append(
                    {
                        "module": persona_ep.name,
                        "persona_class": None,
                        "traceback": tb_str,
                    }
                )
                continue

        if len(persona_classes) > 0:
            elapsed_time_ms = (time_ns() - start_time_ns) // 1000000
            self.log.info(
                f"SUCCESS: Loaded {len(persona_classes)} AI persona classes from entry points. Time elapsed: {elapsed_time_ms}ms."
            )
        else:
            self.log.error(
                "ERROR: Jupyter AI has no AI personas available. "
                + "Please verify your server configuration and open a new issue on our GitHub repo if this warning persists."
            )

        PersonaManager._ep_persona_classes = persona_classes

    def _init_local_persona_classes(self) -> None:
        """
        Load persona classes from local filesystem, storing them as a list in
        `self._local_persona_classes`.

        The `_init_personas()` method should be called after this method to
        re-initialize `self.personas` using the new set of local persona
        classes.
        """
        dotjupyter_dir = self.get_dotjupyter_dir()
        if dotjupyter_dir is None:
            self.log.info("No .jupyter directory found for loading local personas.")
        else:
            self._local_persona_classes = load_from_dir(dotjupyter_dir, self.log)

    def _init_personas(self) -> dict[str, BasePersona]:
        """
        Initializes the list of persona instances for the YChat instance passed
        to the constructor.
        """
        # Ensure that persona classes were initialized first
        persona_classes = []
        if isinstance(PersonaManager._ep_persona_classes, list):
            persona_classes.extend(PersonaManager._ep_persona_classes)
        if isinstance(self._local_persona_classes, list):
            persona_classes.extend(self._local_persona_classes)
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
        for item in persona_classes:
            item.get("module")
            Persona = item.get("persona_class")
            tb = item.get("traceback")
            if Persona is None or tb is not None:
                self._display_persona_error_message(item)
                continue
            try:
                persona = Persona(
                    parent=self,
                    ychat=self.ychat,
                    config_manager=self.config_manager,
                    message_interrupted=self.message_interrupted,
                )
            except Exception:
                tb_str = traceback.format_exc()
                self.log.exception(
                    f"The persona provided by `{Persona.__module__}` "
                    f"raised an exception while instantiating, "
                    f"printed below.\n {tb_str}"
                )
                self._display_persona_error_message(
                    {
                        "module": Persona.__module__,
                        "persona_class": Persona,
                        "traceback": tb_str,
                    }
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


    def _display_persona_error_message(self, persona_item: dict) -> None:
        tb = persona_item.get("traceback")
        if tb is None:
            return
        body = f"Loading an AI persona raised an exception:\n\n```python\n{tb}```"
        self.send_system_message(body)
    

    def send_system_message(self, body: str) -> None:
        """
        Sends a system message to the chat.
        """
        # Set a 'System' user use it to send the message
        with self.ychat._ydoc.transaction():
            self.ychat.set_user(user=User(
                username=SYSTEM_USERNAME,
                name="System",
                display_name="System"
            ))
            self.ychat.add_message(NewMessage(body=body, sender=SYSTEM_USERNAME))
        
        # Hide 'System' user from `@`-mention menu by removing the user. This
        # has to wait a second to allow the frontend to render the system user
        # before removing it.
        # TODO: allow users to be hidden from `@`-mentions, possibly based on
        # username. Currently this will show 'User undefined' after reloading a
        # chat with a system message.
        async def _remove_system_user():
            await asyncio.sleep(1)
            try:
                self.ychat._yusers.pop(SYSTEM_USERNAME)
            except KeyError:
                pass
        asyncio.create_task(_remove_system_user())


    @property
    def personas(self) -> dict[str, BasePersona]:
        """
        Returns a dictionary of all available persona instances, keyed by
        persona ID.
        """
        return self._personas
    

    @property
    def default_persona(self) -> BasePersona | None:
        if not self.default_persona_id:
            return None
        return self.personas.get(self.default_persona_id)


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
        Method that routes an incoming message to the correct personas by
        calling their `process_message()` methods.

        - If the message contains a slash command, the slash command will be
          dispatched to `route_slash_command()` first. If the slash command is
          unrecognized, the message will be handled as a normal message.

        - If the chat has multiple users, then each persona only replies
          when `@`-mentioned.

        - If there is only one user, the last mentioned persona replies
          unless another persona is `@`-mentioned. The last mentioned persona
          defaults to `PersonaManager.default_persona` after starting the server.

        - If only one persona exists as well, then the persona always replies,
          regardless of whether it is `@`-mentioned.
        """

        # Dispatch message to `route_slash_command()` if the first word is a
        # slash command. Return immediately if the slash command is recognized.
        first_word = get_first_word(new_message.body)
        if first_word and first_word.startswith('/'):
            slash_cmd_recognized = self.route_slash_command(new_message)
            if slash_cmd_recognized:
                return

        # Gather routing context
        human_users = self.get_active_human_users()
        sender_not_human = is_persona(new_message.sender) or new_message.sender == SYSTEM_USERNAME
        sender_is_human = not sender_not_human
        mentioned_personas = self.get_mentioned_personas(new_message)
        human_user_count = len(human_users)
        persona_count = len(self.personas)

        # Multi-user case & non-human message case: only route message to
        # mentioned personas
        if sender_not_human or human_user_count > 1:
            if mentioned_personas:
                self._broadcast(new_message, to_personas=mentioned_personas)
            return

        # Single user + multiple personas case: route message to mentioned
        # personas if present. Otherwise route message to last mentioned
        # persona, falling back to the default set by the
        # `PersonaManager.default_persona_id` configurable trait.
        if persona_count > 1:
            # Update last mentioned persona 
            if mentioned_personas and sender_is_human:
                self.last_mentioned_persona = mentioned_personas[0]

            default_persona = self.last_mentioned_persona or self.default_persona
            targeted_personas = mentioned_personas
            if default_persona and not targeted_personas:
                targeted_personas = [default_persona]
            self._broadcast(new_message, to_personas=targeted_personas)
            return

        # Default case (single user, 0/1 personas): persona always replies if present
        self._broadcast(new_message, to_personas=self.personas)
        return
    

    def _broadcast(self, message: Message, *, to_personas: list[BasePersona] | dict[str, BasePersona]) -> None:
        """
        Broadcasts a message to all personas in a given list or dictionary.
        """
        persona_list: list[BasePersona] = to_personas if isinstance(to_personas, list) else list(to_personas.values())
        for persona in persona_list:
            self.event_loop.create_task(persona.process_message(message))
        return


    def route_slash_command(self, new_message: Message) -> bool:
        """
        Routes & handles a message containing a slash command. Returns `True` if
        the message specified a valid slash command recognized by
        `PersonaManager`, `False` otherwise. Notes:

        - Each message may have exactly one slash command, which must be
        specified by the first word of the message.

        - This method will return `True` even if the command was not handled
        successfully. `False` is just meant to indicate that the control flow
        should return back to `route_message()`. This allows AI personas to
        receive custom slash commands that only they recognize.
        """
        first_word = get_first_word(new_message.body)
        assert first_word and first_word.startswith('/')

        command_id = first_word[1:]
        if command_id == "refresh-personas":
            self.handle_refresh_personas_command(new_message)
            return True

        # If command is unrecognized, log an error
        self.log.warning(f"Unrecognized slash command: '/{command_id}'")
        return False


    def handle_refresh_personas_command(self, _: Message) -> None:
        """
        Handles the '/refresh-personas' slash command.
        
        TODO: How do we show status/completion in the UI?
        """
        self.log.info(f"Received '/refresh-personas'. Refreshing personas in chat '{self.room_id}'...")

        # Refresh personas in background task
        asyncio.create_task(self._refresh_personas())
    

    async def _refresh_personas(self):
        # Shutdown all personas
        await self.shutdown_personas()
        
        # Refresh local personas and re-initialize persona instances
        self._init_local_persona_classes()
        self._personas = self._init_personas()

        # Write success message to chat & logs
        self.send_system_message("Refreshed all AI personas in this chat.")
        self.log.info(f"Refreshed all AI personas in chat '{self.room_id}'.")


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

    def get_active_human_users(self):
        """Returns active human users in a chat session"""
        users = []
        for value in [k for k in self.ychat.awareness.states.values()]:
            if "user" in value.keys() and not is_persona(value["user"]["username"]):
                users.append(value["user"])

        return users
    
    async def shutdown_personas(self):
        """
        Shuts down each persona. See `BasePersona.shutdown()` for more info.
        This instance can be restarted by calling `self._init_personas()`.

        This method will be called when `/refresh-personas` is run, and may be
        called when the server is shutting down or when a chat session is
        closed.
        """
        # First, free all transaction locks on the YDoc by awaiting the YChat
        # background tasks first. These tasks run concurrently, so awaiting each
        # in serial has no performance drawback.
        # Without this, `/refresh-personas` causes a runtime error.
        while self.ychat._background_tasks:
            task = next(iter(self.ychat._background_tasks))
            await task
            self.ychat._background_tasks.discard(task)
        
        # Then, shut down each persona
        for persona in self.personas.values():
            persona.shutdown()
        

def is_persona(username: str):
    """Returns true if username belongs to a persona"""
    return username.startswith("jupyter-ai-personas")


def load_from_dir(dir: str, log: Logger) -> list[dict]:
    """
    Load _persona class declarations_ from Python files in the local filesystem.

    Those class declarations are then used to instantiate personas by the
    `PersonaManager`.

    Scans the dir for .py files containing `persona` in their name that do
    _not_ start with a single `_` (i.e. private modules are skipped). Then, it
    dynamically imports them, and extracts any class declarations that are
    subclasses of `BasePersona`.

     Args:
        dir: Directory to scan for persona Python files.
        log: Logger instance for logging messages.

     Returns:
        List of `BasePersona` subclasses found in the directory.
    """
    persona_classes: list[dict] = []

    log.info(f"Searching for persona files in {dir}")
    # Check if root directory exists
    if not os.path.exists(dir):
        return persona_classes

    # Find all .py files in the root directory that contain "persona" in the name
    try:
        all_py_files = glob(os.path.join(dir, "*.py"))
        py_files = []
        for f in all_py_files:
            fname_lower = Path(f).stem.lower()
            if "persona" in fname_lower and not (
                fname_lower.startswith("_") or fname_lower.startswith(".")
            ):
                py_files.append(f)

    except Exception as e:
        # On exception with glob operation, return empty list
        log.error(
            f"{type(e).__name__} occurred while searching for Python files in {dir}"
        )
        return persona_classes

    if py_files:
        log.info(f"Found files from {dir}: {[Path(f).name for f in py_files]}")

    # Temporarily add root_dir to sys.path for imports
    dir_in_path = dir in sys.path
    if not dir_in_path:
        sys.path.insert(0, dir)

    try:
        # For each .py file, dynamically import the module and extract all
        # BasePersona subclasses.
        for py_file in py_files:
            try:
                # Get module name from file path
                module_name = Path(py_file).stem

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
                        log.info(f"Found persona class '{obj.__name__}' in '{py_file}'")
                        persona_classes.append(
                            {"module": py_file, "persona_class": obj, "traceback": None}
                        )

            except Exception:
                # On exception, log error and continue to next file
                tb_str = traceback.format_exc()
                log.exception(
                    f"Unable to load persona classes from '{py_file}', exception details printed below.\n{tb_str}"
                )
                persona_classes.append(
                    {"module": py_file, "persona_class": None, "traceback": tb_str}
                )
                continue
    finally:
        # Remove root_dir from sys.path if we added it
        if not dir_in_path and dir in sys.path:
            sys.path.remove(dir)

    return persona_classes


def get_first_word(input_str: str) -> str | None:
    """
    Finds the first word in a given string, ignoring leading whitespace.
    
    Returns the first word, or None if there is no first word.
    """
    start = 0
    
    # Skip leading whitespace
    while start < len(input_str) and input_str[start].isspace():
        start += 1
    
    # Find end of first word
    end = start
    while end < len(input_str) and not input_str[end].isspace():
        end += 1
    
    first_word = input_str[start:end]
    return first_word if first_word else None

