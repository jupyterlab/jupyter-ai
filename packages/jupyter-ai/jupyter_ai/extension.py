import time

from dask.distributed import Client as DaskClient
from jupyter_ai.chat_handlers.learn import Retriever
from jupyter_ai_magics.utils import get_em_providers, get_lm_providers
from jupyter_server.extension.application import ExtensionApp

from .chat_handlers import (
    AskChatHandler,
    ClearChatHandler,
    DefaultChatHandler,
    GenerateChatHandler,
    HelpChatHandler,
    LearnChatHandler,
)
from .chat_handlers.help import HelpMessage
from .config_manager import ConfigManager
from .handlers import (
    ApiKeysHandler,
    ChatHistoryHandler,
    EmbeddingsModelProviderHandler,
    GlobalConfigHandler,
    ModelProviderHandler,
    RootChatHandler,
)


class AiExtension(ExtensionApp):
    name = "jupyter_ai"
    handlers = [
        (r"api/ai/api_keys/(?P<api_key_name>\w+)", ApiKeysHandler),
        (r"api/ai/config/?", GlobalConfigHandler),
        (r"api/ai/chats/?", RootChatHandler),
        (r"api/ai/chats/history?", ChatHistoryHandler),
        (r"api/ai/providers?", ModelProviderHandler),
        (r"api/ai/providers/embeddings?", EmbeddingsModelProviderHandler),
    ]

    def initialize_settings(self):
        start = time.time()

        self.settings["lm_providers"] = get_lm_providers(log=self.log)
        self.settings["em_providers"] = get_em_providers(log=self.log)

        self.settings["jai_config_manager"] = ConfigManager(
            # traitlets configuration, not JAI configuration.
            config=self.config,
            log=self.log,
            lm_providers=self.settings["lm_providers"],
            em_providers=self.settings["em_providers"],
        )

        self.log.info("Registered providers.")

        self.log.info(f"Registered {self.name} server extension")

        # Store chat clients in a dictionary
        self.settings["chat_clients"] = {}
        self.settings["jai_root_chat_handlers"] = {}

        # list of chat messages to broadcast to new clients
        # this is only used to render the UI, and is not the conversational
        # memory object used by the LM chain.
        self.settings["chat_history"] = [HelpMessage()]

        # get reference to event loop
        # `asyncio.get_event_loop()` is deprecated in Python 3.11+, in favor of
        # the more readable `asyncio.get_event_loop_policy().get_event_loop()`.
        # it's easier to just reference the loop directly.
        loop = self.serverapp.io_loop.asyncio_loop
        self.settings["jai_event_loop"] = loop

        # We cannot instantiate the Dask client directly here because it
        # requires the event loop to be running on init. So instead we schedule
        # this as a task that is run as soon as the loop starts, and pass
        # consumers a Future that resolves to the Dask client when awaited.
        dask_client_future = loop.create_task(self._get_dask_client())

        # initialize chat handlers
        chat_handler_kwargs = {
            "log": self.log,
            "config_manager": self.settings["jai_config_manager"],
            "root_chat_handlers": self.settings["jai_root_chat_handlers"],
        }
        default_chat_handler = DefaultChatHandler(
            **chat_handler_kwargs, chat_history=self.settings["chat_history"]
        )
        clear_chat_handler = ClearChatHandler(
            **chat_handler_kwargs, chat_history=self.settings["chat_history"]
        )
        generate_chat_handler = GenerateChatHandler(
            **chat_handler_kwargs,
            root_dir=self.serverapp.root_dir,
        )
        learn_chat_handler = LearnChatHandler(
            **chat_handler_kwargs,
            root_dir=self.serverapp.root_dir,
            dask_client_future=dask_client_future,
        )
        help_chat_handler = HelpChatHandler(**chat_handler_kwargs)
        retriever = Retriever(learn_chat_handler=learn_chat_handler)
        ask_chat_handler = AskChatHandler(**chat_handler_kwargs, retriever=retriever)
        self.settings["jai_chat_handlers"] = {
            "default": default_chat_handler,
            "/ask": ask_chat_handler,
            "/clear": clear_chat_handler,
            "/generate": generate_chat_handler,
            "/learn": learn_chat_handler,
            "/help": help_chat_handler,
        }

        latency_ms = round((time.time() - start) * 1000)
        self.log.info(f"Initialized Jupyter AI server extension in {latency_ms} ms.")

    async def _get_dask_client(self):
        return DaskClient(processes=False, asynchronous=True)
