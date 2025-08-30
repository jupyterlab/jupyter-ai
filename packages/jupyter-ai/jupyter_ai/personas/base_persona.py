from __future__ import annotations
import asyncio
import os
from abc import ABC, ABCMeta, abstractmethod
from dataclasses import asdict
from logging import Logger
from time import time
from typing import TYPE_CHECKING, Any, Optional

from jupyter_ai.config_manager import ConfigManager
from jupyterlab_chat.models import Message, NewMessage, User
from jupyterlab_chat.ychat import YChat
from litellm import ModelResponseStream, supports_function_calling
from litellm.utils import function_to_dict
from pydantic import BaseModel
from traitlets import MetaHasTraits
from traitlets.config import LoggingConfigurable

from .persona_awareness import PersonaAwareness
from ..litellm_lib import ToolCallList, StreamResult, run_tools
from ..tools.default_toolkit import DEFAULT_TOOLKIT

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

    async def stream_message(
        self, reply_stream: "AsyncIterator[ModelResponseStream | str]"
    ) -> StreamResult:
        """
        Takes an async iterator, dubbed the 'reply stream', and streams it to a
        new message by this persona in the YChat. The async iterator may yield
        either strings or `litellm.ModelResponseStream` objects. Details:

        - Creates a new message upon receiving the first chunk from the reply
        stream, then continuously updates it until the stream is closed.

        - Automatically manages its awareness state to show writing status.

        Returns a list of `ResolvedToolCall` objects. If this list is not empty,
        the persona should run these tools.
        """
        stream_id: Optional[str] = None
        stream_interrupted = False
        tool_call_list = ToolCallList()
        try:
            self.awareness.set_local_state_field("isWriting", True)

            async for chunk in reply_stream:
                # Start the stream with an empty message on the initial reply.
                # Bind the new message ID to `stream_id`.
                if not stream_id:
                    stream_id = self.ychat.add_message(
                        NewMessage(body="", sender=self.id)
                    )
                    self.message_interrupted[stream_id] = asyncio.Event()
                    self.awareness.set_local_state_field("isWriting", stream_id)
                assert stream_id

                # Compute `content_delta` and `tool_calls_delta` based on the
                # type of object yielded by `reply_stream`.
                if isinstance(chunk, ModelResponseStream):
                    delta = chunk.choices[0].delta
                    content_delta = delta.content
                    toolcalls_delta = delta.tool_calls
                elif isinstance(chunk, str):
                    content_delta = chunk
                    toolcalls_delta = None
                else:
                    raise Exception(f"Unrecognized type in stream_message(): {type(chunk)}")

                # LiteLLM streams always terminate with an empty chunk, so 
                # continue in this case.
                if not (content_delta or toolcalls_delta):
                    continue

                # Terminate the stream if the user requested it.
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

                # Append `content_delta` to the existing message.
                if content_delta:
                    self.ychat.update_message(
                        Message(
                            id=stream_id,
                            body=content_delta,
                            time=time(),
                            sender=self.id,
                            raw_time=False,
                        ),
                        append=True,
                    )
                if toolcalls_delta:
                    tool_call_list += toolcalls_delta
            
        except Exception as e:
            self.log.error(
                f"Persona '{self.name}' encountered an exception printed below when attempting to stream output."
            )
            self.log.exception(e)
        finally:
            # Reset local state
            self.awareness.set_local_state_field("isWriting", False)
            self.message_interrupted.pop(stream_id, None)

            # If stream was interrupted, add a tombstone and return `[]`,
            # indicating that no tools should be run afterwards.
            if stream_id and stream_interrupted:
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
                    return None
            
            # TODO: determine where this should live
            count = len(tool_call_list)
            if count > 0:
                self.log.info(f"AI response triggered {count} tool calls.")

            return StreamResult(
                id=stream_id,
                tool_call_list=tool_call_list
            )
            

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
    
    def process_attachments(self, message: Message) -> Optional[str]:
        """
        Process file attachments in the message and return their content as a string.
        """

        if not message.attachments:
            return None

        context_parts = []

        for attachment_id in message.attachments:
            self.log.info(f"FILE: Processing attachment with ID: {attachment_id}")
            try:
                # Try to resolve attachment using multiple strategies
                file_path = self.resolve_attachment_to_path(attachment_id)

                if not file_path:
                    self.log.warning(
                        f"Could not resolve attachment ID: {attachment_id}"
                    )
                    continue

                # Read the file content
                with open(file_path, encoding="utf-8") as f:
                    file_content = f.read()

                # Get relative path for display
                rel_path = os.path.relpath(file_path, self.get_workspace_dir())

                # Add file content with header
                context_parts.append(f"File: {rel_path}\n```\n{file_content}\n```")

            except Exception as e:
                self.log.warning(f"Failed to read attachment {attachment_id}: {e}")
                context_parts.append(
                    f"Attachment: {attachment_id} (could not read file: {e})"
                )

        result = "\n\n".join(context_parts) if context_parts else None
        return result

    def resolve_attachment_to_path(self, attachment_id: str) -> Optional[str]:
        """
        Resolve an attachment ID to its file path using multiple strategies.
        """

        try:
            attachment_data = self.ychat.get_attachments().get(attachment_id)

            if attachment_data and isinstance(attachment_data, dict):
                # If attachment has a 'value' field with filename
                if "value" in attachment_data:
                    filename = attachment_data["value"]

                    # Try relative to workspace directory
                    workspace_path = os.path.join(self.get_workspace_dir(), filename)
                    if os.path.exists(workspace_path):
                        return workspace_path

                    # Try as absolute path
                    if os.path.exists(filename):
                        return filename

            return None

        except Exception as e:
            self.log.error(f"Failed to resolve attachment {attachment_id}: {e}")
            return None

    def get_tools(self, model_id: str) -> list[dict]:
        """
        Returns the `tools` parameter which should be passed to
        `litellm.acompletion()` for a given LiteLLM model ID.

        If the model does not support tool-calling, this method returns an empty
        list. Otherwise, it returns the list of tools available in the current
        environment. These may include:

        - The default set of tool functions in Jupyter AI, defined in the
        the default toolkit from `jupyter_ai.tools`.

        - (TODO) Tools provided by MCP server configuration, if any.

        - (TODO) Web search.

        - (TODO) File search using vector store IDs.

        TODO: cache this

        TODO: Implement some permissions system so users can control what tools
        are allowable.

        NOTE: The returned list is expected by LiteLLM to conform to the `tools`
        parameter defintiion defined by the OpenAI API:
        https://platform.openai.com/docs/guides/tools#available-tools

        NOTE: This API is a WIP and is very likely to change.
        """
        # Return early if the model does not support tool calling
        if not supports_function_calling(model=model_id):
            return []

        tool_descriptions = []

        # Get all tools from the default toolkit and store their object descriptions
        for tool in DEFAULT_TOOLKIT.get_tools():
            # Here, we are using a util function from LiteLLM to coerce
            # each `Tool` struct into a tool description dictionary expected
            # by LiteLLM.
            desc = {
                "type": "function",
                "function": function_to_dict(tool.callable),
            }
            tool_descriptions.append(desc)
        
        # Finally, return the tool descriptions
        self.log.info(tool_descriptions)
        return tool_descriptions
    

    async def run_tools(self, tool_call_list: ToolCallList) -> list[dict]:
        """
        Runs the tools specified in a given tool call list using the default
        toolkit.
        """
        tool_outputs = await run_tools(tool_call_list, toolkit=DEFAULT_TOOLKIT)
        self.log.info(f"Ran {len(tool_outputs)} tool functions.")
        return tool_outputs


    
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
