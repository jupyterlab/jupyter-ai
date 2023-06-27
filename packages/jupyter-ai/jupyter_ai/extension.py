from importlib_metadata import entry_points
from jupyter_ai.config_manager import ConfigManager
from jupyter_ai_magics.utils import get_lm_providers, get_em_providers
from jupyter_server.extension.application import ExtensionApp
from jupyter_ai.chat_handlers import AskChatHandler, ClearChatHandler, DefaultChatHandler, GenerateChatHandler, LearnChatHandler

from .handlers import (
    RootChatHandler,
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
        (r"api/ai/chats/?", RootChatHandler),
        (r"api/ai/chats/history?", ChatHistoryHandler),
        (r"api/ai/providers?", ModelProviderHandler),
        (r"api/ai/providers/embeddings?", EmbeddingsModelProviderHandler),
    ]

    def initialize_settings(self):
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
        self.settings["jai_root_chat_handlers"] = {}

        # store chat messages in memory for now
        # this is only used to render the UI, and is not the conversational
        # memory object used by the LM chain.
        self.settings["chat_history"] = []

        # initialize chat handlers
        chat_handler_kwargs = {
            "log": self.log,
            "config_manager": self.settings["jai_config_manager"],
            "root_chat_handlers": self.settings["jai_root_chat_handlers"]
        }
        default_chat_handler = DefaultChatHandler(**chat_handler_kwargs, chat_history=self.settings["chat_history"])
        clear_chat_handler = ClearChatHandler(**chat_handler_kwargs)
        generate_chat_handler = GenerateChatHandler(**chat_handler_kwargs, root_dir=self.serverapp.root_dir)
        learn_chat_handler = LearnChatHandler(**chat_handler_kwargs, root_dir=self.serverapp.root_dir)
        ask_chat_handler = AskChatHandler(**chat_handler_kwargs, retriever=learn_chat_handler)
        self.settings["jai_chat_handlers"] = {
            "default": default_chat_handler,
            "/ask": ask_chat_handler,
            "/clear": clear_chat_handler,
            "/generate": generate_chat_handler,
            "/learn": learn_chat_handler,
        }
