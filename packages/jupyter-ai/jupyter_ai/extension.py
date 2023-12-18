import logging
import re
import time

from dask.distributed import Client as DaskClient
from importlib_metadata import entry_points
from jupyter_ai.chat_handlers.learn import Retriever
from jupyter_ai_magics.utils import get_em_providers, get_lm_providers
from jupyter_server.extension.application import ExtensionApp
from traitlets import Dict, List, Unicode

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

    allowed_providers = List(
        Unicode(),
        default_value=None,
        help="Identifiers of allowlisted providers. If `None`, all are allowed.",
        allow_none=True,
        config=True,
    )

    blocked_providers = List(
        Unicode(),
        default_value=None,
        help="Identifiers of blocklisted providers. If `None`, none are blocked.",
        allow_none=True,
        config=True,
    )

    allowed_models = List(
        Unicode(),
        default_value=None,
        help="""
        Language models to allow, as a list of global model IDs in the format
        `<provider>:<local-model-id>`. If `None`, all are allowed. Defaults to
        `None`.

        Note: Currently, if `allowed_providers` is also set, then this field is
        ignored. This is subject to change in a future non-major release. Using
        both traits is considered to be undefined behavior at this time.
        """,
        allow_none=True,
        config=True,
    )

    blocked_models = List(
        Unicode(),
        default_value=None,
        help="""
        Language models to block, as a list of global model IDs in the format
        `<provider>:<local-model-id>`. If `None`, none are blocked. Defaults to
        `None`.
        """,
        allow_none=True,
        config=True,
    )

    model_parameters = Dict(
        key_trait=Unicode(),
        value_trait=Dict(),
        default_value={},
        help="""Key-value pairs for model id and corresponding parameters that
        are passed to the provider class. The values are unpacked and passed to
        the provider class as-is.""",
        allow_none=True,
        config=True,
    )

    error_logs_dir = Unicode(
        default_value=None,
        help="""Path to a directory where the error logs should be
        written to. Defaults to `jupyter-ai-logs/` in the preferred dir
        (if defined) or in root dir otherwise.""",
        allow_none=True,
        config=True,
    )

    def initialize_settings(self):
        start = time.time()

        # Read from allowlist and blocklist
        restrictions = {
            "allowed_providers": self.allowed_providers,
            "blocked_providers": self.blocked_providers,
        }
        self.settings["allowed_models"] = self.allowed_models
        self.settings["blocked_models"] = self.blocked_models
        self.log.info(f"Configured provider allowlist: {self.allowed_providers}")
        self.log.info(f"Configured provider blocklist: {self.blocked_providers}")
        self.log.info(f"Configured model allowlist: {self.allowed_models}")
        self.log.info(f"Configured model blocklist: {self.blocked_models}")

        self.settings["model_parameters"] = self.model_parameters
        self.log.info(f"Configured model parameters: {self.model_parameters}")

        # Fetch LM & EM providers
        self.settings["lm_providers"] = get_lm_providers(
            log=self.log, restrictions=restrictions
        )
        self.settings["em_providers"] = get_em_providers(
            log=self.log, restrictions=restrictions
        )

        self.settings["jai_config_manager"] = ConfigManager(
            # traitlets configuration, not JAI configuration.
            config=self.config,
            log=self.log,
            lm_providers=self.settings["lm_providers"],
            em_providers=self.settings["em_providers"],
            allowed_providers=self.allowed_providers,
            blocked_providers=self.blocked_providers,
            allowed_models=self.allowed_models,
            blocked_models=self.blocked_models,
        )

        self.log.info("Registered providers.")

        self.log.info(f"Registered {self.name} server extension")

        # Store chat clients in a dictionary
        self.settings["chat_clients"] = {}
        self.settings["jai_root_chat_handlers"] = {}

        # list of chat messages to broadcast to new clients
        # this is only used to render the UI, and is not the conversational
        # memory object used by the LM chain.
        self.settings["chat_history"] = []

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

        eps = entry_points()
        # initialize chat handlers
        chat_handler_eps = eps.select(group="jupyter_ai.chat_handlers")

        chat_handler_kwargs = {
            "log": self.log,
            "config_manager": self.settings["jai_config_manager"],
            "root_chat_handlers": self.settings["jai_root_chat_handlers"],
            "chat_history": self.settings["chat_history"],
            "root_dir": self.serverapp.root_dir,
            "dask_client_future": dask_client_future,
            "model_parameters": self.settings["model_parameters"],
        }
        default_chat_handler = DefaultChatHandler(**chat_handler_kwargs)
        clear_chat_handler = ClearChatHandler(**chat_handler_kwargs)
        generate_chat_handler = GenerateChatHandler(
            **chat_handler_kwargs,
            preferred_dir=self.serverapp.contents_manager.preferred_dir,
            log_dir=self.error_logs_dir,
        )
        learn_chat_handler = LearnChatHandler(**chat_handler_kwargs)
        retriever = Retriever(learn_chat_handler=learn_chat_handler)
        ask_chat_handler = AskChatHandler(**chat_handler_kwargs, retriever=retriever)

        jai_chat_handlers = {
            "default": default_chat_handler,
            "/ask": ask_chat_handler,
            "/clear": clear_chat_handler,
            "/generate": generate_chat_handler,
            "/learn": learn_chat_handler,
        }

        help_chat_handler = HelpChatHandler(
            **chat_handler_kwargs, chat_handlers=jai_chat_handlers
        )

        slash_command_pattern = r"^[a-zA-Z0-9_]+$"
        for chat_handler_ep in chat_handler_eps:
            try:
                chat_handler = chat_handler_ep.load()
            except Exception as err:
                self.log.error(
                    f"Unable to load chat handler class from entry point `{chat_handler_ep.name}`: "
                    + f"Unexpected {err=}, {type(err)=}"
                )
                continue

            if chat_handler.routing_type.routing_method == "slash_command":
                # Each slash ID must be used only once.
                # Slash IDs may contain only alphanumerics and underscores.
                slash_id = chat_handler.routing_type.slash_id

                if slash_id is None:
                    self.log.error(
                        f"Handler `{chat_handler_ep.name}` has an invalid slash command "
                        + f"`None`; only the default chat handler may use this"
                    )
                    continue

                # Validate slash ID (/^[A-Za-z0-9_]+$/)
                if re.match(slash_command_pattern, slash_id):
                    command_name = f"/{slash_id}"
                else:
                    self.log.error(
                        f"Handler `{chat_handler_ep.name}` has an invalid slash command "
                        + f"`{slash_id}`; must contain only letters, numbers, "
                        + "and underscores"
                    )
                    continue

            if command_name in jai_chat_handlers:
                self.log.error(
                    f"Unable to register chat handler `{chat_handler.id}` because command `{command_name}` already has a handler"
                )
                continue

            # The entry point is a class; we need to instantiate the class to send messages to it
            jai_chat_handlers[command_name] = chat_handler(**chat_handler_kwargs)
            self.log.info(
                f"Registered chat handler `{chat_handler.id}` with command `{command_name}`."
            )

        # Make help always appear as the last command
        jai_chat_handlers["/help"] = help_chat_handler

        self.settings["chat_history"].append(
            HelpMessage(chat_handlers=jai_chat_handlers)
        )
        self.settings["jai_chat_handlers"] = jai_chat_handlers

        latency_ms = round((time.time() - start) * 1000)
        self.log.info(f"Initialized Jupyter AI server extension in {latency_ms} ms.")

    async def _get_dask_client(self):
        return DaskClient(processes=False, asynchronous=True)
