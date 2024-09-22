import getpass
import json
import time
import uuid
from asyncio import AbstractEventLoop
from dataclasses import asdict
from typing import TYPE_CHECKING, Dict, List, Optional, cast

import tornado
from jupyter_ai.chat_handlers import BaseChatHandler, SlashCommandRoutingType
from jupyter_ai.config_manager import ConfigManager, KeyEmptyError, WriteConflictError
from jupyter_ai.context_providers import BaseCommandContextProvider, ContextCommand
from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from jupyter_server.base.handlers import JupyterHandler
from langchain.pydantic_v1 import ValidationError
from tornado import web, websocket
from tornado.web import HTTPError

from .models import (
    AgentChatMessage,
    AgentStreamChunkMessage,
    AgentStreamMessage,
    ChatClient,
    ChatHistory,
    ChatMessage,
    ChatRequest,
    ChatUser,
    ClearMessage,
    ClearRequest,
    ClosePendingMessage,
    ConnectionMessage,
    HumanChatMessage,
    ListOptionsEntry,
    ListOptionsResponse,
    ListProvidersEntry,
    ListProvidersResponse,
    ListSlashCommandsEntry,
    ListSlashCommandsResponse,
    Message,
    PendingMessage,
    UpdateConfigRequest,
)

if TYPE_CHECKING:
    from jupyter_ai_magics.embedding_providers import BaseEmbeddingsProvider
    from jupyter_ai_magics.providers import BaseProvider

    from .context_providers import BaseCommandContextProvider
    from .history import BoundedChatHistory


class ChatHistoryHandler(BaseAPIHandler):
    """Handler to return message history"""

    @property
    def chat_history(self) -> List[ChatMessage]:
        return self.settings["chat_history"]

    @property
    def pending_messages(self) -> List[PendingMessage]:
        return self.settings["pending_messages"]

    @tornado.web.authenticated
    async def get(self):
        history = ChatHistory(
            messages=self.chat_history, pending_messages=self.pending_messages
        )
        self.finish(history.json())


class RootChatHandler(JupyterHandler, websocket.WebSocketHandler):
    """
    A websocket handler for chat.
    """

    @property
    def root_chat_handlers(self) -> Dict[str, "RootChatHandler"]:
        """Dictionary mapping client IDs to their corresponding RootChatHandler
        instances."""
        return self.settings["jai_root_chat_handlers"]

    @property
    def chat_handlers(self) -> Dict[str, "BaseChatHandler"]:
        """Dictionary mapping chat commands to their corresponding
        BaseChatHandler instances."""
        return self.settings["jai_chat_handlers"]

    @property
    def chat_clients(self) -> Dict[str, ChatClient]:
        """Dictionary mapping client IDs to their ChatClient objects that store
        metadata."""
        return self.settings["chat_clients"]

    @property
    def chat_client(self) -> ChatClient:
        """Returns ChatClient object associated with the current connection."""
        return self.chat_clients[self.client_id]

    @property
    def chat_history(self) -> List[ChatMessage]:
        return self.settings["chat_history"]

    @chat_history.setter
    def chat_history(self, new_history):
        self.settings["chat_history"] = new_history

    @property
    def llm_chat_memory(self) -> "BoundedChatHistory":
        return self.settings["llm_chat_memory"]

    @property
    def loop(self) -> AbstractEventLoop:
        return self.settings["jai_event_loop"]

    @property
    def pending_messages(self) -> List[PendingMessage]:
        return self.settings["pending_messages"]

    @pending_messages.setter
    def pending_messages(self, new_pending_messages):
        self.settings["pending_messages"] = new_pending_messages

    def initialize(self):
        self.log.debug("Initializing websocket connection %s", self.request.path)

    def pre_get(self):
        """Handles authentication/authorization."""
        # authenticate the request before opening the websocket
        user = self.current_user
        if user is None:
            self.log.warning("Couldn't authenticate WebSocket connection")
            raise web.HTTPError(403)

        # authorize the user.
        if not self.authorizer.is_authorized(self, user, "execute", "events"):
            raise web.HTTPError(403)

    async def get(self, *args, **kwargs):
        """Get an event socket."""
        self.pre_get()
        res = super().get(*args, **kwargs)
        await res

    def get_chat_user(self) -> ChatUser:
        """Retrieves the current user. If `jupyter_collaboration` is not
        installed, one is synthesized from the server's current shell
        environment."""
        # Get a dictionary of all loaded extensions.
        # (`serverapp` is a property on all `JupyterHandler` subclasses)
        assert self.serverapp
        extensions = self.serverapp.extension_manager.extensions
        collaborative = (
            "jupyter_collaboration" in extensions
            and extensions["jupyter_collaboration"].enabled
        )

        if collaborative:
            names = self.current_user.name.split(" ", maxsplit=2)
            initials = getattr(self.current_user, "initials", None)
            if not initials:
                # compute default initials in case IdentityProvider doesn't
                # return initials, e.g. JupyterHub (#302)
                names = self.current_user.name.split(" ", maxsplit=2)
                initials = "".join(
                    [(name.capitalize()[0] if len(name) > 0 else "") for name in names]
                )
            chat_user_kwargs = {
                **asdict(self.current_user),
                "initials": initials,
            }

            return ChatUser(**chat_user_kwargs)

        login = getpass.getuser()
        initials = login[0].capitalize()
        return ChatUser(
            username=login,
            initials=initials,
            name=login,
            display_name=login,
            color=None,
            avatar_url=None,
        )

    def generate_client_id(self):
        """Generates a client ID to identify the current WS connection."""
        return uuid.uuid4().hex

    def open(self):
        """Handles opening of a WebSocket connection. Client ID can be retrieved
        from `self.client_id`."""

        current_user = self.get_chat_user().dict()
        client_id = self.generate_client_id()

        self.root_chat_handlers[client_id] = self
        self.chat_clients[client_id] = ChatClient(**current_user, id=client_id)
        self.client_id = client_id
        self.write_message(
            ConnectionMessage(
                client_id=client_id,
                history=ChatHistory(
                    messages=self.chat_history, pending_messages=self.pending_messages
                ),
            ).dict()
        )

        self.log.info(f"Client connected. ID: {client_id}")
        self.log.debug("Clients are : %s", self.root_chat_handlers.keys())

    def broadcast_message(self, message: Message):
        """Broadcasts message to all connected clients.
        Appends message to chat history.
        """

        # do not broadcast agent messages that are replying to cleared human message
        if (
            isinstance(message, (AgentChatMessage, AgentStreamMessage))
            and message.reply_to
        ):
            if message.reply_to not in [
                m.id for m in self.chat_history if isinstance(m, HumanChatMessage)
            ]:
                return

        self.log.debug("Broadcasting message: %s to all clients...", message)
        client_ids = self.root_chat_handlers.keys()

        for client_id in client_ids:
            client = self.root_chat_handlers[client_id]
            if client:
                client.write_message(message.dict())

        # append all messages of type `ChatMessage` directly to the chat history
        if isinstance(
            message, (HumanChatMessage, AgentChatMessage, AgentStreamMessage)
        ):
            self.chat_history.append(message)
        elif isinstance(message, AgentStreamChunkMessage):
            # for stream chunks, modify the corresponding `AgentStreamMessage`
            # by appending its content and potentially marking it as complete.
            chunk: AgentStreamChunkMessage = message

            # iterate backwards from the end of the list
            for history_message in self.chat_history[::-1]:
                if (
                    history_message.type == "agent-stream"
                    and history_message.id == chunk.id
                ):
                    stream_message: AgentStreamMessage = history_message
                    stream_message.body += chunk.content
                    stream_message.complete = chunk.stream_complete
                    break
        elif isinstance(message, PendingMessage):
            self.pending_messages.append(message)
        elif isinstance(message, ClosePendingMessage):
            self.pending_messages = list(
                filter(lambda m: m.id != message.id, self.pending_messages)
            )
        elif isinstance(message, ClearMessage):
            if message.targets:
                self._clear_chat_history_at(message.targets)
            else:
                self.chat_history.clear()
                self.pending_messages.clear()
                self.llm_chat_memory.clear()
                self.settings["jai_chat_handlers"]["default"].send_help_message()

    async def on_message(self, message):
        self.log.debug("Message received: %s", message)

        try:
            message = json.loads(message)
            if message.get("type") == "clear":
                request = ClearRequest(**message)
            else:
                request = ChatRequest(**message)
        except ValidationError as e:
            self.log.error(e)
            return

        if isinstance(request, ClearRequest):
            if not request.target:
                targets = None
            elif request.after:
                target_msg = None
                for msg in self.chat_history:
                    if msg.id == request.target:
                        target_msg = msg
                if target_msg:
                    targets = [
                        msg.id
                        for msg in self.chat_history
                        if msg.time >= target_msg.time and msg.type == "human"
                    ]
            else:
                targets = [request.target]
            self.broadcast_message(ClearMessage(targets=targets))
            return

        chat_request = request
        message_body = chat_request.prompt
        if chat_request.selection:
            message_body += f"\n\n```\n{chat_request.selection.source}\n```\n"

        # message broadcast to chat clients
        chat_message_id = str(uuid.uuid4())
        chat_message = HumanChatMessage(
            id=chat_message_id,
            time=time.time(),
            body=message_body,
            prompt=chat_request.prompt,
            selection=chat_request.selection,
            client=self.chat_client,
        )

        # broadcast the message to other clients
        self.broadcast_message(message=chat_message)

        # do not await this, as it blocks the parent task responsible for
        # handling messages from a websocket.  instead, process each message
        # as a distinct concurrent task.
        self.loop.create_task(self._route(chat_message))

    async def _route(self, message):
        """Method that routes an incoming message to the appropriate handler."""
        default = self.chat_handlers["default"]
        # Split on any whitespace, either spaces or newlines
        maybe_command = message.body.split(None, 1)[0]
        is_command = (
            message.body.startswith("/")
            and maybe_command in self.chat_handlers.keys()
            and maybe_command != "default"
        )
        command = maybe_command if is_command else "default"

        start = time.time()
        if is_command:
            await self.chat_handlers[command].on_message(message)
        else:
            await default.on_message(message)

        latency_ms = round((time.time() - start) * 1000)
        command_readable = "Default" if command == "default" else command
        self.log.info(f"{command_readable} chat handler resolved in {latency_ms} ms.")

    def _clear_chat_history_at(self, msg_ids: List[str]):
        """
        Clears conversation exchanges associated with list of human message IDs.
        """
        self.chat_history[:] = [
            msg
            for msg in self.chat_history
            if msg.id not in msg_ids and getattr(msg, "reply_to", None) not in msg_ids
        ]
        self.pending_messages[:] = [
            msg for msg in self.pending_messages if msg.reply_to not in msg_ids
        ]
        self.llm_chat_memory.clear(msg_ids)

    def on_close(self):
        self.log.debug("Disconnecting client with user %s", self.client_id)

        self.root_chat_handlers.pop(self.client_id, None)
        self.chat_clients.pop(self.client_id, None)

        self.log.info(f"Client disconnected. ID: {self.client_id}")
        self.log.debug("Chat clients: %s", self.root_chat_handlers.keys())


class ProviderHandler(BaseAPIHandler):
    """
    Helper base class used for HTTP handlers hosting endpoints relating to
    providers. Wrapper around BaseAPIHandler.
    """

    @property
    def lm_providers(self) -> Dict[str, "BaseProvider"]:
        return self.settings["lm_providers"]

    @property
    def em_providers(self) -> Dict[str, "BaseEmbeddingsProvider"]:
        return self.settings["em_providers"]

    @property
    def allowed_models(self) -> Optional[List[str]]:
        return self.settings["allowed_models"]

    @property
    def blocked_models(self) -> Optional[List[str]]:
        return self.settings["blocked_models"]

    def _filter_blocked_models(self, providers: List[ListProvidersEntry]):
        """
        Satisfy the model-level allow/blocklist by filtering models accordingly.
        The provider-level allow/blocklist is already handled in
        `AiExtension.initialize_settings()`.
        """
        if self.blocked_models is None and self.allowed_models is None:
            return providers

        def filter_predicate(local_model_id: str):
            model_id = provider.id + ":" + local_model_id
            if self.blocked_models:
                return model_id not in self.blocked_models
            else:
                return model_id in cast(List, self.allowed_models)

        # filter out every model w/ model ID according to allow/blocklist
        for provider in providers:
            provider.models = list(filter(filter_predicate, provider.models or []))
            provider.chat_models = list(
                filter(filter_predicate, provider.chat_models or [])
            )
            provider.completion_models = list(
                filter(filter_predicate, provider.completion_models or [])
            )

        # filter out every provider with no models which satisfy the allow/blocklist, then return
        return filter((lambda p: len(p.models) > 0), providers)


class ModelProviderHandler(ProviderHandler):
    @web.authenticated
    def get(self):
        providers = []

        # Step 1: gather providers
        for provider in self.lm_providers.values():
            optionals = {}
            if provider.model_id_label:
                optionals["model_id_label"] = provider.model_id_label

            providers.append(
                ListProvidersEntry(
                    id=provider.id,
                    name=provider.name,
                    models=provider.models,
                    chat_models=provider.chat_models(),
                    completion_models=provider.completion_models(),
                    help=provider.help,
                    auth_strategy=provider.auth_strategy,
                    registry=provider.registry,
                    fields=provider.fields,
                    **optionals,
                )
            )

        # Step 2: sort & filter providers
        providers = self._filter_blocked_models(providers)
        providers = sorted(providers, key=lambda p: p.name)

        # Finally, yield response.
        response = ListProvidersResponse(providers=providers)
        self.finish(response.json())


class EmbeddingsModelProviderHandler(ProviderHandler):
    @web.authenticated
    def get(self):
        providers = []
        for provider in self.em_providers.values():
            providers.append(
                ListProvidersEntry(
                    id=provider.id,
                    name=provider.name,
                    models=provider.models,
                    auth_strategy=provider.auth_strategy,
                    registry=provider.registry,
                    fields=provider.fields,
                )
            )

        providers = self._filter_blocked_models(providers)
        providers = sorted(providers, key=lambda p: p.name)

        response = ListProvidersResponse(providers=providers)
        self.finish(response.json())


class GlobalConfigHandler(BaseAPIHandler):
    """API handler for fetching and setting the
    model and emebddings config.
    """

    @property
    def config_manager(self):
        return self.settings["jai_config_manager"]

    @web.authenticated
    def get(self):
        config = self.config_manager.get_config()
        if not config:
            raise HTTPError(500, "No config found.")

        self.finish(config.json())

    @web.authenticated
    def post(self):
        try:
            config = UpdateConfigRequest(**self.get_json_body())
            self.config_manager.update_config(config)
            self.set_status(204)
            self.finish()
        except (ValidationError, WriteConflictError, KeyEmptyError) as e:
            self.log.exception(e)
            raise HTTPError(500, str(e)) from e
        except ValueError as e:
            self.log.exception(e)
            raise HTTPError(500, str(e.cause) if hasattr(e, "cause") else str(e))
        except Exception as e:
            self.log.exception(e)
            raise HTTPError(
                500, "Unexpected error occurred while updating the config."
            ) from e


class ApiKeysHandler(BaseAPIHandler):
    @property
    def config_manager(self) -> ConfigManager:  # type:ignore[override]
        return self.settings["jai_config_manager"]

    @web.authenticated
    def delete(self, api_key_name: str):
        try:
            self.config_manager.delete_api_key(api_key_name)
        except Exception as e:
            raise HTTPError(500, str(e))


class SlashCommandsInfoHandler(BaseAPIHandler):
    """List slash commands that are currently available to the user."""

    @property
    def config_manager(self) -> ConfigManager:  # type:ignore[override]
        return self.settings["jai_config_manager"]

    @property
    def chat_handlers(self) -> Dict[str, "BaseChatHandler"]:
        return self.settings["jai_chat_handlers"]

    @web.authenticated
    def get(self):
        response = ListSlashCommandsResponse()

        # if no selected LLM, return an empty response
        if not self.config_manager.lm_provider:
            self.finish(response.json())
            return

        for id, chat_handler in self.chat_handlers.items():
            # filter out any chat handler that is not a slash command
            if (
                id == "default"
                or chat_handler.routing_type.routing_method != "slash_command"
            ):
                continue

            # hint the type of this attribute
            routing_type: SlashCommandRoutingType = chat_handler.routing_type

            # filter out any chat handler that is unsupported by the current LLM
            if (
                "/" + routing_type.slash_id
                in self.config_manager.lm_provider.unsupported_slash_commands
            ):
                continue

            response.slash_commands.append(
                ListSlashCommandsEntry(
                    slash_id=routing_type.slash_id, description=chat_handler.help
                )
            )

        # sort slash commands by slash id and deliver the response
        response.slash_commands.sort(key=lambda sc: sc.slash_id)
        self.finish(response.json())


class AutocompleteOptionsHandler(BaseAPIHandler):
    """List context that are currently available to the user."""

    @property
    def config_manager(self) -> ConfigManager:  # type:ignore[override]
        return self.settings["jai_config_manager"]

    @property
    def context_providers(self) -> Dict[str, "BaseCommandContextProvider"]:
        return self.settings["jai_context_providers"]

    @property
    def chat_handlers(self) -> Dict[str, "BaseChatHandler"]:
        return self.settings["jai_chat_handlers"]

    @web.authenticated
    def get(self):
        response = ListOptionsResponse()

        # if no selected LLM, return an empty response
        if not self.config_manager.lm_provider:
            self.finish(response.json())
            return

        partial_cmd = self.get_query_argument("partialCommand", None)
        if partial_cmd:
            # if providing options for partial command argument
            cmd = ContextCommand(cmd=partial_cmd)
            context_provider = next(
                (
                    cp
                    for cp in self.context_providers.values()
                    if isinstance(cp, BaseCommandContextProvider)
                    and cp.command_id == cmd.id
                ),
                None,
            )
            if (
                cmd.arg is not None
                and context_provider
                and isinstance(context_provider, BaseCommandContextProvider)
            ):
                response.options = context_provider.get_arg_options(cmd.arg)
        else:
            response.options = (
                self._get_slash_command_options() + self._get_context_provider_options()
            )
        self.finish(response.json())

    def _get_slash_command_options(self) -> List[ListOptionsEntry]:
        options = []
        for id, chat_handler in self.chat_handlers.items():
            # filter out any chat handler that is not a slash command
            if id == "default" or not isinstance(
                chat_handler.routing_type, SlashCommandRoutingType
            ):
                continue

            routing_type = chat_handler.routing_type

            # filter out any chat handler that is unsupported by the current LLM
            if (
                not routing_type.slash_id
                or "/" + routing_type.slash_id
                in self.config_manager.lm_provider.unsupported_slash_commands
            ):
                continue

            options.append(
                self._make_autocomplete_option(
                    id="/" + routing_type.slash_id,
                    description=chat_handler.help,
                    only_start=True,
                    requires_arg=False,
                )
            )
        options.sort(key=lambda opt: opt.id)
        return options

    def _get_context_provider_options(self) -> List[ListOptionsEntry]:
        options = [
            self._make_autocomplete_option(
                id=context_provider.command_id,
                description=context_provider.help,
                only_start=context_provider.only_start,
                requires_arg=context_provider.requires_arg,
            )
            for context_provider in self.context_providers.values()
            if isinstance(context_provider, BaseCommandContextProvider)
        ]
        options.sort(key=lambda opt: opt.id)
        return options

    def _make_autocomplete_option(
        self,
        id: str,
        description: str,
        only_start: bool,
        requires_arg: bool,
    ):
        label = id + (":" if requires_arg else " ")
        return ListOptionsEntry(
            id=id, description=description, label=label, only_start=only_start
        )
