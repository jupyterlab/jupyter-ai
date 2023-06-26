import asyncio

import ray
from importlib_metadata import entry_points
from jupyter_ai.actors.ask import AskActor
from jupyter_ai.actors.base import ACTOR_TYPE
from jupyter_ai.actors.default import DefaultActor
from jupyter_ai.actors.generate import GenerateActor
from jupyter_ai.actors.learn import LearnActor
from jupyter_ai.reply_processor import ReplyProcessor
from jupyter_ai.config_manager import ConfigManager
from jupyter_ai_magics.utils import get_lm_providers, get_em_providers
from jupyter_server.extension.application import ExtensionApp
from ray.util.queue import Queue

from .engine import BaseModelEngine
from .handlers import (
    ChatHandler,
    ChatHistoryHandler,
    EmbeddingsModelProviderHandler,
    GlobalConfigHandler,
    ModelProviderHandler,
    PromptAPIHandler,
    TaskAPIHandler,
)


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

    def initialize_settings(self):
        ray.init()

        # EP := entry point
        eps = entry_points()

        ## load default tasks and bind them to settings
        module_default_tasks_eps = eps.select(group="jupyter_ai.default_tasks")

        if not module_default_tasks_eps:
            self.settings["ai_default_tasks"] = []
            return

        default_tasks = []
        for module_default_tasks_ep in module_default_tasks_eps:
            try:
                module_default_tasks = module_default_tasks_ep.load()
            except:
                self.log.error(
                    f"Unable to load task from entry point `{module_default_tasks_ep.name}`"
                )
                continue

            default_tasks += module_default_tasks

        self.settings["ai_default_tasks"] = default_tasks
        self.log.info("Registered all default tasks.")

        self.settings["lm_providers"] = get_lm_providers(log=self.log)
        self.settings["em_providers"] = get_em_providers(log=self.log)
        
        self.settings["jai_config_manager"] = ConfigManager(
            log=self.log,
            lm_providers=self.settings["lm_providers"],
            em_providers=self.settings["em_providers"]
        )

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

        default_actor = DefaultActor.options(name=ACTOR_TYPE.DEFAULT.value).remote(
            reply_queue=reply_queue,
            log=self.log,
            chat_history=self.settings["chat_history"],
            config_manager=self.settings["jai_config_manager"]
        )

        learn_actor = LearnActor.options(name=ACTOR_TYPE.LEARN.value).remote(
            reply_queue=reply_queue,
            log=self.log,
            root_dir=self.serverapp.root_dir,
            config_manager=self.settings["jai_config_manager"]
        )
        ask_actor = AskActor.options(name=ACTOR_TYPE.ASK.value).remote(
            reply_queue=reply_queue,
            log=self.log,
            config_manager=self.settings["jai_config_manager"]
        )
        generate_actor = GenerateActor.options(name=ACTOR_TYPE.GENERATE.value).remote(
            reply_queue=reply_queue,
            log=self.log,
            root_dir=self.settings["server_root_dir"],
            config_manager=self.settings["jai_config_manager"]
        )

        self.settings["default_actor"] = default_actor
        self.settings["learn_actor"] = learn_actor
        self.settings["ask_actor"] = ask_actor
        self.settings["generate_actor"] = generate_actor

        reply_processor = ReplyProcessor(
            self.settings["chat_handlers"], reply_queue, log=self.log
        )
        loop = asyncio.get_event_loop()
        loop.create_task(reply_processor.start())
