import json

import tornado
from tornado.web import HTTPError
from pydantic import ValidationError

from tornado import web, websocket

from jupyter_server.base.handlers import APIHandler as BaseAPIHandler, JupyterHandler
from jupyter_server.utils import ensure_async
from .task_manager import TaskManager
from .models import PromptRequest, ChatRequest
from langchain.schema import messages_to_dict

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

class ChatAPIHandler(APIHandler):
    @tornado.web.authenticated
    async def post(self):
        try:
            request = ChatRequest(**self.get_json_body())
        except ValidationError as e:
            self.log.exception(e)
            raise HTTPError(500, str(e)) from e
        
        if not self.openai_chat:
            raise HTTPError(500, "No chat models available.")
        
        result = await ensure_async(self.openai_chat.agenerate([request.prompt]))
        output = result.generations[0][0].text
        self.openai_chat.append_exchange(request.prompt, output)

        self.finish(json.dumps({
            "output": output,
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
    def chat_provider(self):
        if self._chat_provider is None:
            self._chat_provider = self.settings["chat_provider"]
        return self._chat_provider
    
    @property
    def chat_message_queue(self):
        if self._chat_message_queue is None:
            self._chat_message_queue = self.settings["chat_message_queue"]
        return self._chat_message_queue
    
    def add_chat_client(self, username):
        self.settings["chat_clients"][username] = self
        self.log.debug("Clients are : %s", self.settings["chat_clients"])

    def remove_chat_client(self, username):
        self.settings["chat_clients"][username] = None

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

    def open(self):
        # send the full message history to the new client
        self.log.debug("Connected...")
        self.log.debug("current user is %s", self.current_user)
        self.add_chat_client(self.current_user.username)
        history = messages_to_dict(self.chat_provider.memory.chat_memory.messages)
        if history:
            event = {
                "event": "history",
                "data": history
            }
            self.write_message(json.dumps(event))

    def on_message(self, message):
        self.log.debug("message received: %s", message)
        # Push to the queue
        #self.chat_message_queue.push(message)

        message = json.loads(message)

        event = {
            "event": "message",
            "data": message
        }
        data = json.dumps(event)
        # broadcast the message to other clients
        client_names = self.settings["chat_clients"].keys()
        for username in client_names:
            if username != self.current_user.username:
                self.settings["chat_clients"][username].write_message(data)

        # process the message
        response = self.chat_provider.predict(input=message["prompt"])

        event = {
            "event": "reply",
            "data": response
        }
        # broadcast to all clients
        for username in client_names:
            self.settings["chat_clients"][username].write_message(json.dumps(event))
        

    def on_close(self):
        self.log.debug("Disconnected client %s", self.current_user)
        self.remove_chat_client(self.current_user.username)
