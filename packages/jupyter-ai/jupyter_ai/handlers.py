import getpass
import json
import time
import uuid
from asyncio import AbstractEventLoop
from dataclasses import asdict
from typing import Dict, List

import tornado
from jupyter_ai.chat_handlers import BaseChatHandler
from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from jupyter_server.base.handlers import JupyterHandler
from pydantic import ValidationError
from tornado import web, websocket
from tornado.web import HTTPError

from .models import (
    AgentChatMessage,
    ChatClient,
    ChatHistory,
    ChatMessage,
    ChatRequest,
    ChatUser,
    ConnectionMessage,
    GlobalConfig,
    HumanChatMessage,
    ListProvidersEntry,
    ListProvidersResponse,
    Message,
)


class ChatHistoryHandler(BaseAPIHandler):
    """Handler to return message history"""

    _messages = []

    @property
    def chat_history(self):
        return self.settings["chat_history"]

    @chat_history.setter
    def _chat_history_setter(self, new_history):
        self.settings["chat_history"] = new_history

    @tornado.web.authenticated
    async def get(self):
        history = ChatHistory(messages=self.chat_history)
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

    @property
    def loop(self) -> AbstractEventLoop:
        return self.settings["jai_event_loop"]

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
        """Retrieves the current user. If collaborative mode is disabled, one
        is synthesized from the login."""
        collaborative = self.config.get("LabApp", {}).get("collaborative", False)

        if collaborative:
            return ChatUser(**asdict(self.current_user))

        login = getpass.getuser()
        return ChatUser(
            username=login,
            initials=login[0].capitalize(),
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
        self.write_message(ConnectionMessage(client_id=client_id).dict())

        self.log.info(f"Client connected. ID: {client_id}")
        self.log.debug("Clients are : %s", self.root_chat_handlers.keys())

    def broadcast_message(self, message: Message):
        """Broadcasts message to all connected clients.
        Appends message to `self.chat_history`.
        """

        self.log.debug("Broadcasting message: %s to all clients...", message)
        client_ids = self.root_chat_handlers.keys()

        for client_id in client_ids:
            client = self.root_chat_handlers[client_id]
            if client:
                client.write_message(message.dict())

        # Only append ChatMessage instances to history, not control messages
        if isinstance(message, HumanChatMessage) or isinstance(
            message, AgentChatMessage
        ):
            self.chat_history.append(message)

    async def on_message(self, message):
        self.log.debug("Message recieved: %s", message)

        try:
            message = json.loads(message)
            chat_request = ChatRequest(**message)
        except ValidationError as e:
            self.log.error(e)
            return

        # message broadcast to chat clients
        chat_message_id = str(uuid.uuid4())
        chat_message = HumanChatMessage(
            id=chat_message_id,
            time=time.time(),
            body=chat_request.prompt,
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
        maybe_command = message.body.split(" ", 1)[0]
        is_command = (
            message.body.startswith("/")
            and maybe_command in self.chat_handlers.keys()
            and maybe_command != "default"
        )
        command = maybe_command if is_command else "default"

        start = time.time()
        if is_command:
            await self.chat_handlers[command].process_message(message)
        else:
            await default.process_message(message)

        latency_ms = round((time.time() - start) * 1000)
        command_readable = "Default" if command == "default" else command
        self.log.info(f"{command_readable} chat handler resolved in {latency_ms} ms.")

    def on_close(self):
        self.log.debug("Disconnecting client with user %s", self.client_id)

        self.root_chat_handlers.pop(self.client_id, None)
        self.chat_clients.pop(self.client_id, None)

        self.log.info(f"Client disconnected. ID: {self.client_id}")
        self.log.debug("Chat clients: %s", self.root_chat_handlers.keys())


class ModelProviderHandler(BaseAPIHandler):
    @property
    def lm_providers(self):
        return self.settings["lm_providers"]

    @web.authenticated
    def get(self):
        providers = []
        for provider in self.lm_providers.values():
            # skip old legacy OpenAI chat provider used only in magics
            if provider.id == "openai-chat":
                continue

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

        response = ListProvidersResponse(
            providers=sorted(providers, key=lambda p: p.name)
        )
        self.finish(response.json())


class EmbeddingsModelProviderHandler(BaseAPIHandler):
    @property
    def em_providers(self):
        return self.settings["em_providers"]

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

        response = ListProvidersResponse(
            providers=sorted(providers, key=lambda p: p.name)
        )
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
            config = GlobalConfig(**self.get_json_body())
            self.config_manager.update(config)
            self.set_status(204)
            self.finish()
        except ValidationError as e:
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
