import json

import tornado
from tornado.web import HTTPError
from pydantic import ValidationError

from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from jupyter_server.utils import ensure_async
from .task_manager import TaskManager
from .models import PromptRequest, ChatRequest

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
