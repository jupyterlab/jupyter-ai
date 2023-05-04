import asyncio

from jupyter_ai.actors.chat_provider import ChatProviderActor
from jupyter_ai.actors.config import ConfigActor
from jupyter_ai.actors.embeddings_provider import EmbeddingsProviderActor
from jupyter_ai.actors.providers import ProvidersActor

from jupyter_ai_magics.utils import load_providers

from langchain.memory import ConversationBufferWindowMemory
from jupyter_ai.actors.default import DefaultActor 
from jupyter_ai.actors.ask import AskActor 
from jupyter_ai.actors.learn import LearnActor
from jupyter_ai.actors.router import Router
from jupyter_ai.actors.memory import MemoryActor
from jupyter_ai.actors.generate import GenerateActor
from jupyter_ai.actors.base import ACTOR_TYPE
from jupyter_ai.reply_processor import ReplyProcessor
from jupyter_server.extension.application import ExtensionApp

from .handlers import (
    ChatHandler, 
    ChatHistoryHandler, 
    EmbeddingsModelProviderHandler, 
    ModelProviderHandler, 
    PromptAPIHandler, 
    TaskAPIHandler,
    GlobalConfigHandler
)

from importlib_metadata import entry_points
import inspect
from .engine import BaseModelEngine

import ray
from ray.util.queue import Queue
from jupyter_ai_magics.utils import load_providers


class AiExtension(ExtensionApp):
    name = "jupyter_ai"
    handlers = [
        ("api/ai/config", GlobalConfigHandler),
        ("api/ai/prompt", PromptAPIHandler),
        (r"api/ai/tasks/?", TaskAPIHandler),
        (r"api/ai/tasks/([\w\-:]*)", TaskAPIHandler),
        (r"api/ai/chats/?", ChatHandler),
        (r"api/ai/chats/history?", ChatHistoryHandler),
        (r"api/ai/providers?", ModelProviderHandler),
        (r"api/ai/providers/embeddings?", EmbeddingsModelProviderHandler),
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

        providers = load_providers(log=self.log)
        self.settings["chat_providers"] = providers
        self.log.info("Registered providers.")

        self.log.info(f"Registered {self.name} server extension")

        # Store chat clients in a dictionary
        self.settings["chat_clients"] = {}
        self.settings["chat_handlers"] = {}
        
        # store chat messages in memory for now
        # this is only used to render the UI, and is not the conversational
        # memory object used by the LM chain.
        self.settings["chat_history"] = []


        reply_queue = Queue()
        self.settings["reply_queue"] = reply_queue

        router = Router.options(name=ACTOR_TYPE.ROUTER).remote(
            reply_queue=reply_queue,
            log=self.log,
        )
        default_actor = DefaultActor.options(name=ACTOR_TYPE.DEFAULT.value).remote(
            reply_queue=reply_queue, 
            log=self.log,
            chat_history=self.settings["chat_history"]
        )

        providers_actor = ProvidersActor.options(name=ACTOR_TYPE.PROVIDERS.value).remote(
            log=self.log,
        )
        config_actor = ConfigActor.options(name=ACTOR_TYPE.CONFIG.value).remote(
            log=self.log,
        )
        chat_provider_actor = ChatProviderActor.options(name=ACTOR_TYPE.CHAT_PROVIDER.value).remote(
            log=self.log,
        )
        embeddings_provider_actor = EmbeddingsProviderActor.options(name=ACTOR_TYPE.EMBEDDINGS_PROVIDER.value).remote(
            log=self.log,
        )
        learn_actor = LearnActor.options(name=ACTOR_TYPE.LEARN.value).remote(
            reply_queue=reply_queue,
            log=self.log,
            root_dir=self.serverapp.root_dir,
        )
        ask_actor = AskActor.options(name=ACTOR_TYPE.ASK.value).remote(
            reply_queue=reply_queue, 
            log=self.log,
        )
        memory_actor = MemoryActor.options(name=ACTOR_TYPE.MEMORY.value).remote(
            log=self.log,
            memory=ConversationBufferWindowMemory(return_messages=True, k=2),
        )
        generate_actor = GenerateActor.options(name=ACTOR_TYPE.GENERATE.value).remote(
            reply_queue=reply_queue, 
            log=self.log,
            root_dir=self.settings['server_root_dir'],
        )
     
        self.settings['router'] = router
        self.settings['providers_actor'] = providers_actor
        self.settings['config_actor'] = config_actor
        self.settings['chat_provider_actor'] = chat_provider_actor
        self.settings['embeddings_provider_actor'] = embeddings_provider_actor
        self.settings["default_actor"] = default_actor
        self.settings["learn_actor"] = learn_actor
        self.settings["ask_actor"] = ask_actor
        self.settings["memory_actor"] = memory_actor
        self.settings["generate_actor"] = generate_actor

        reply_processor = ReplyProcessor(self.settings['chat_handlers'], reply_queue, log=self.log)        
        loop = asyncio.get_event_loop()
        loop.create_task(reply_processor.start())            