import asyncio
import queue
from jupyter_ai.actors import DefaultActor, FileSystemActor
from jupyter_ai.reply_processor import ReplyProcessor
from jupyter_server.extension.application import ExtensionApp
from .handlers import ChatHandler, ChatHistoryHandler, PromptAPIHandler, TaskAPIHandler
from importlib_metadata import entry_points
import inspect
from .engine import BaseModelEngine
from jupyter_ai_magics.providers import ChatOpenAIProvider

import ray
from ray.util.queue import Queue


class AiExtension(ExtensionApp):
    name = "jupyter_ai"
    handlers = [
        ("api/ai/prompt", PromptAPIHandler),
        (r"api/ai/tasks/?", TaskAPIHandler),
        (r"api/ai/tasks/([\w\-:]*)", TaskAPIHandler),
        (r"api/ai/chats/?", ChatHandler),
        (r"api/ai/chats/history?", ChatHistoryHandler),
    ]

    @property
    def ai_engines(self): 
        if "ai_engines" not in self.settings:
            self.settings["ai_engines"] = {}

        return self.settings["ai_engines"]
    

    def initialize_settings(self):
        ray.init()

        # EP := entry point
        eps = entry_points()
        
        ## step 1: instantiate model engines and bind them to settings
        model_engine_class_eps = eps.select(group="jupyter_ai.model_engine_classes")
        
        if not model_engine_class_eps:
            self.log.error("No model engines found for jupyter_ai.model_engine_classes group. One or more model engines are required for AI extension to work.")
            return

        for model_engine_class_ep in model_engine_class_eps:
            try:
                Engine = model_engine_class_ep.load()
            except:
                self.log.error(f"Unable to load model engine class from entry point `{model_engine_class_ep.name}`.")
                continue

            if not inspect.isclass(Engine) or not issubclass(Engine, BaseModelEngine):
                self.log.error(f"Unable to instantiate model engine class from entry point `{model_engine_class_ep.name}` as it is not a subclass of `BaseModelEngine`.")
                continue

            try:
                self.ai_engines[Engine.id] = Engine(config=self.config, log=self.log)
            except:
                self.log.error(f"Unable to instantiate model engine class from entry point `{model_engine_class_ep.name}`.")
                continue

            self.log.info(f"Registered engine `{Engine.id}`.")

        ## step 2: load default tasks and bind them to settings
        module_default_tasks_eps = eps.select(group="jupyter_ai.default_tasks")

        if not module_default_tasks_eps:
            self.settings["ai_default_tasks"] = []
            return
        
        default_tasks = []
        for module_default_tasks_ep in module_default_tasks_eps:
            try:
                module_default_tasks = module_default_tasks_ep.load()
            except:
                self.log.error(f"Unable to load task from entry point `{module_default_tasks_ep.name}`")
                continue
            
            default_tasks += module_default_tasks

        self.settings["ai_default_tasks"] = default_tasks
        self.log.info("Registered all default tasks.")

        ## load OpenAI provider
        self.settings["openai_chat"] = ChatOpenAIProvider(model_id="gpt-3.5-turbo")

        self.log.info(f"Registered {self.name} server extension")

        # Add a message queue to the settings to be used by the chat handler
        self.settings["chat_message_queue"] = queue.Queue()

        # Store chat clients in a dictionary
        self.settings["chat_clients"] = {}
        self.settings["chat_handlers"] = {}
        
        # store chat messages in memory for now
        self.settings["chat_history"] = []

        reply_queue = Queue()
        self.settings["reply_queue"] = reply_queue

        fs_actor = FileSystemActor.options(name="filesystem").remote(reply_queue)
        default_actor = DefaultActor.options(name="default").remote(reply_queue)
        self.settings["fs_actor"] = fs_actor
        self.settings["default_actor"] = default_actor

        reply_processor = ReplyProcessor(self.settings['chat_handlers'], reply_queue, log=self.log)        
        loop = asyncio.get_event_loop()
        loop.create_task(reply_processor.start())