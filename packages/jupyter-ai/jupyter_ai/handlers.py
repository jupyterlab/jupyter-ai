from dataclasses import asdict
import json
from typing import Dict, List
import ray
import tornado
import uuid
import time

from tornado.web import HTTPError
from pydantic import ValidationError

from tornado import web, websocket

from jupyter_server.base.handlers import APIHandler as BaseAPIHandler, JupyterHandler
from jupyter_server.utils import ensure_async

from .task_manager import TaskManager
from .models import ChatHistory, PromptRequest, ChatRequest, ChatMessage, Message, AgentChatMessage, HumanChatMessage, ConnectionMessage, ChatClient


class APIHandler(BaseAPIHandler):
    @property
    def engines(self): 
        return self.settings["ai_engines"]
    
    @property
    def default_tasks(self):
        return self.settings["ai_default_tasks"]

    @property
    def task_manager(self):
        # we have to create the TaskManager lazily, since no event loop is
        # running in ServerApp.initialize_settings().
        if "task_manager" not in self.settings:
            self.settings["task_manager"] = TaskManager(engines=self.engines, default_tasks=self.default_tasks)
        return self.settings["task_manager"]
    
    @property
    def openai_chat(self):
        return self.settings["openai_chat"]
    
class PromptAPIHandler(APIHandler):
    @tornado.web.authenticated
    async def post(self):
        try:
            request = PromptRequest(**self.get_json_body())
        except ValidationError as e:
            self.log.exception(e)
            raise HTTPError(500, str(e)) from e

        if request.engine_id not in self.engines:
            raise HTTPError(500, f"Model engine not registered: {request.engine_id}")

        engine = self.engines[request.engine_id]
        task = await self.task_manager.describe_task(request.task_id)
        if not task:
            raise HTTPError(404, f"Task not found with ID: {request.task_id}")
        
        output = await ensure_async(engine.execute(task, request.prompt_variables))

        self.finish(json.dumps({
            "output": output,
            "insertion_mode": task.insertion_mode
        }))

class TaskAPIHandler(APIHandler):
    @tornado.web.authenticated
    async def get(self, id=None):
        if id is None:
            list_tasks_response = await self.task_manager.list_tasks()
            self.finish(json.dumps(list_tasks_response.dict()))
            return
        
        describe_task_response = await self.task_manager.describe_task(id)
        if describe_task_response is None:
            raise HTTPError(404, f"Task not found with ID: {id}")

        self.finish(json.dumps(describe_task_response.dict()))


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


class ChatHandler(
    JupyterHandler,
    websocket.WebSocketHandler
):
    """
    A websocket handler for chat.
    """

    _chat_provider = None  
    _chat_message_queue = None 
    
    @property
    def chat_message_queue(self):
        if self._chat_message_queue is None:
            self._chat_message_queue = self.settings["chat_message_queue"]
        return self._chat_message_queue
    
    @property
    def chat_handlers(self) -> Dict[str, 'ChatHandler']:
        """Dictionary mapping client IDs to their WebSocket handler
        instances."""
        return self.settings["chat_handlers"]
    
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

    def initialize(self):
        self.log.debug("Initializing websocket connection %s", self.request.path)

    def pre_get(self):
        """Handles authentication/authorization.
        """
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

    def generate_client_id(self):
        """Generates a client ID to identify the current WS connection."""
        # if collaborative mode is enabled, each client already has a UUID
        # collaborative = self.config.get("LabApp", {}).get("collaborative", False)
        # if collaborative:
        #     return self.current_user.username

        # if collaborative mode is not enabled, each client is assigned a UUID
        return uuid.uuid4().hex

    def open(self):
        """Handles opening of a WebSocket connection. Client ID can be retrieved
        from `self.client_id`."""

        client_id = self.generate_client_id()

        self.chat_handlers[client_id] = self
        self.chat_clients[client_id] = ChatClient(**asdict(self.current_user), id=client_id)
        self.client_id = client_id
        self.write_message(ConnectionMessage(client_id=client_id).dict())

        self.log.info(f"Client connected. ID: {client_id}")
        self.log.debug("Clients are : %s", self.chat_handlers.keys())

    def broadcast_message(self, message: Message):
        """Broadcasts message to all connected clients. 
        Appends message to `self.chat_history`.
        """

        self.log.debug("Broadcasting message: %s to all clients...", message)
        client_ids = self.chat_handlers.keys()
        
        for client_id in client_ids:
            client = self.chat_handlers[client_id]
            if client:
                client.write_message(message.dict())
        
        # Only append ChatMessage instances to history, not control messages
        if isinstance(message, HumanChatMessage) or isinstance(message, AgentChatMessage):
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

        # Clear the message history if given the /clear command
        if chat_request.prompt.startswith('/'):
            command = chat_request.prompt.split(' ', 1)[0]
            if command == '/clear':
                self.chat_history.clear()

        # process through the router
        router = ray.get_actor("router")
        router.route_message.remote(chat_message)

    def on_close(self):
        self.log.debug("Disconnecting client with user %s", self.client_id)

        self.chat_handlers.pop(self.client_id, None)
        self.chat_clients.pop(self.client_id, None)

        self.log.info(f"Client disconnected. ID: {self.client_id}")
        self.log.debug("Chat clients: %s", self.chat_handlers.keys())
