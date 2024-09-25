import os
import re
import time
import types

from dask.distributed import Client as DaskClient
from importlib_metadata import entry_points
from jupyter_ai.chat_handlers.learn import Retriever
from jupyter_ai_magics import BaseProvider, JupyternautPersona
from jupyter_ai_magics.utils import get_em_providers, get_lm_providers
from jupyter_server.extension.application import ExtensionApp
from tornado.web import StaticFileHandler
from traitlets import Dict, Integer, List, Unicode

from .chat_handlers import (
    AskChatHandler,
    ClearChatHandler,
    DefaultChatHandler,
    ExportChatHandler,
    FixChatHandler,
    GenerateChatHandler,
    HelpChatHandler,
    LearnChatHandler,
)
from .completions.handlers import DefaultInlineCompletionHandler
from .config_manager import ConfigManager
from .context_providers import BaseCommandContextProvider, FileContextProvider
from .handlers import (
    ApiKeysHandler,
    AutocompleteOptionsHandler,
    ChatHistoryHandler,
    EmbeddingsModelProviderHandler,
    GlobalConfigHandler,
    ModelProviderHandler,
    RootChatHandler,
    SlashCommandsInfoHandler,
)
from .history import BoundedChatHistory

JUPYTERNAUT_AVATAR_ROUTE = JupyternautPersona.avatar_route
JUPYTERNAUT_AVATAR_PATH = str(
    os.path.join(os.path.dirname(__file__), "static", "jupyternaut.svg")
)


DEFAULT_HELP_MESSAGE_TEMPLATE = """Hi there! I'm {persona_name}, your programming assistant.
You can ask me a question using the text box below. You can also use these commands:
{slash_commands_list}

You can use the following commands to add context to your questions:
{context_commands_list}

Jupyter AI includes [magic commands](https://jupyter-ai.readthedocs.io/en/latest/users/index.html#the-ai-and-ai-magic-commands) that you can use in your notebooks.
For more information, see the [documentation](https://jupyter-ai.readthedocs.io).
"""


class AiExtension(ExtensionApp):
    name = "jupyter_ai"
    handlers = [  # type:ignore[assignment]
        (r"api/ai/api_keys/(?P<api_key_name>\w+)", ApiKeysHandler),
        (r"api/ai/config/?", GlobalConfigHandler),
        (r"api/ai/chats/?", RootChatHandler),
        (r"api/ai/chats/history?", ChatHistoryHandler),
        (r"api/ai/chats/slash_commands?", SlashCommandsInfoHandler),
        (r"api/ai/chats/autocomplete_options?", AutocompleteOptionsHandler),
        (r"api/ai/providers?", ModelProviderHandler),
        (r"api/ai/providers/embeddings?", EmbeddingsModelProviderHandler),
        (r"api/ai/completion/inline/?", DefaultInlineCompletionHandler),
        # serve the default persona avatar at this path.
        # the `()` at the end of the URL denotes an empty regex capture group,
        # required by Tornado.
        (
            rf"{JUPYTERNAUT_AVATAR_ROUTE}()",
            StaticFileHandler,
            {"path": JUPYTERNAUT_AVATAR_PATH},
        ),
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

    default_language_model = Unicode(
        default_value=None,
        allow_none=True,
        help="""
        Default language model to use, as string in the format
        <provider-id>:<model-id>, defaults to None.
        """,
        config=True,
    )

    default_embeddings_model = Unicode(
        default_value=None,
        allow_none=True,
        help="""
        Default embeddings model to use, as string in the format
        <provider-id>:<model-id>, defaults to None.
        """,
        config=True,
    )

    default_api_keys = Dict(
        key_trait=Unicode(),
        value_trait=Unicode(),
        default_value=None,
        allow_none=True,
        help="""
        Default API keys for model providers, as a dictionary,
        in the format `<key-name>:<key-value>`. Defaults to None.
        """,
        config=True,
    )

    help_message_template = Unicode(
        default_value=DEFAULT_HELP_MESSAGE_TEMPLATE,
        help="""
        A format string accepted by `str.format()`, which is used to generate a
        dynamic help message. The format string should contain exactly two
        named replacement fields: `persona_name` and `slash_commands_list`.

        - `persona_name`: String containing the name of the persona, which is
        defined by the configured language model. Usually defaults to
        'Jupyternaut'.

        - `slash_commands_list`: A string containing a bulleted list of the
        slash commands available to the configured language model.
        """,
        config=True,
    )

    default_max_chat_history = Integer(
        default_value=2,
        help="""
        Number of chat interactions to keep in the conversational memory object.

        An interaction is defined as an exchange between a human and AI, thus
        comprising of one or two messages.

        Set to `None` to keep all interactions.
        """,
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

        defaults = {
            "model_provider_id": self.default_language_model,
            "embeddings_provider_id": self.default_embeddings_model,
            "api_keys": self.default_api_keys,
            "fields": self.model_parameters,
        }

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
            defaults=defaults,
        )

        # Expose a subset of settings as read-only to the providers
        BaseProvider.server_settings = types.MappingProxyType(
            self.serverapp.web_app.settings
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

        # conversational memory object used by LM chain
        self.settings["llm_chat_memory"] = BoundedChatHistory(
            k=self.default_max_chat_history
        )

        # list of pending messages
        self.settings["pending_messages"] = []

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
        self.settings["dask_client_future"] = loop.create_task(self._get_dask_client())

        # Create empty context providers dict to be filled later.
        # This is created early to use as kwargs for chat handlers.
        self.settings["jai_context_providers"] = {}

        # initialize chat handlers
        self._init_chat_handlers()

        # initialize context providers
        self._init_context_provders()

        # show help message at server start
        self._show_help_message()

        latency_ms = round((time.time() - start) * 1000)
        self.log.info(f"Initialized Jupyter AI server extension in {latency_ms} ms.")

    def _show_help_message(self):
        """
        Method that ensures a dynamically-generated help message is included in
        the chat history shown to users.
        """
        # call `send_help_message()` on any instance of `BaseChatHandler`. The
        # `default` chat handler should always exist, so we reference that
        # object when calling `send_help_message()`.
        default_chat_handler: DefaultChatHandler = self.settings["jai_chat_handlers"][
            "default"
        ]
        default_chat_handler.send_help_message()

    async def _get_dask_client(self):
        return DaskClient(processes=False, asynchronous=True)

    async def stop_extension(self):
        """
        Public method called by Jupyter Server when the server is stopping.
        This calls the cleanup code defined in `self._stop_exception()` inside
        an exception handler, as the server halts if this method raises an
        exception.
        """
        try:
            await self._stop_extension()
        except Exception as e:
            self.log.error("Jupyter AI raised an exception while stopping:")
            self.log.exception(e)

    async def _stop_extension(self):
        """
        Private method that defines the cleanup code to run when the server is
        stopping.
        """
        if "dask_client_future" in self.settings:
            dask_client: DaskClient = await self.settings["dask_client_future"]
            self.log.info("Closing Dask client.")
            await dask_client.close()
            self.log.debug("Closed Dask client.")

    def _init_chat_handlers(self):
        eps = entry_points()
        chat_handler_eps = eps.select(group="jupyter_ai.chat_handlers")
        chat_handlers = {}
        chat_handler_kwargs = {
            "log": self.log,
            "config_manager": self.settings["jai_config_manager"],
            "model_parameters": self.settings["model_parameters"],
            "root_chat_handlers": self.settings["jai_root_chat_handlers"],
            "chat_history": self.settings["chat_history"],
            "llm_chat_memory": self.settings["llm_chat_memory"],
            "root_dir": self.serverapp.root_dir,
            "dask_client_future": self.settings["dask_client_future"],
            "model_parameters": self.settings["model_parameters"],
            "preferred_dir": self.serverapp.contents_manager.preferred_dir,
            "help_message_template": self.help_message_template,
            "chat_handlers": chat_handlers,
            "context_providers": self.settings["jai_context_providers"],
        }
        default_chat_handler = DefaultChatHandler(**chat_handler_kwargs)
        clear_chat_handler = ClearChatHandler(**chat_handler_kwargs)
        generate_chat_handler = GenerateChatHandler(
            **chat_handler_kwargs,
            log_dir=self.error_logs_dir,
        )
        learn_chat_handler = LearnChatHandler(**chat_handler_kwargs)
        retriever = Retriever(learn_chat_handler=learn_chat_handler)
        ask_chat_handler = AskChatHandler(**chat_handler_kwargs, retriever=retriever)

        export_chat_handler = ExportChatHandler(**chat_handler_kwargs)

        fix_chat_handler = FixChatHandler(**chat_handler_kwargs)

        chat_handlers["default"] = default_chat_handler
        chat_handlers["/ask"] = ask_chat_handler
        chat_handlers["/clear"] = clear_chat_handler
        chat_handlers["/generate"] = generate_chat_handler
        chat_handlers["/learn"] = learn_chat_handler
        chat_handlers["/export"] = export_chat_handler
        chat_handlers["/fix"] = fix_chat_handler

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

            if command_name in chat_handlers:
                self.log.error(
                    f"Unable to register chat handler `{chat_handler.id}` because command `{command_name}` already has a handler"
                )
                continue

            # The entry point is a class; we need to instantiate the class to send messages to it
            chat_handlers[command_name] = chat_handler(**chat_handler_kwargs)
            self.log.info(
                f"Registered chat handler `{chat_handler.id}` with command `{command_name}`."
            )

        # Make help always appear as the last command
        chat_handlers["/help"] = HelpChatHandler(**chat_handler_kwargs)

        # bind chat handlers to settings
        self.settings["jai_chat_handlers"] = chat_handlers

    def _init_context_provders(self):
        eps = entry_points()
        context_providers_eps = eps.select(group="jupyter_ai.context_providers")
        context_providers = self.settings["jai_context_providers"]
        context_providers_kwargs = {
            "log": self.log,
            "config_manager": self.settings["jai_config_manager"],
            "model_parameters": self.settings["model_parameters"],
            "chat_history": self.settings["chat_history"],
            "llm_chat_memory": self.settings["llm_chat_memory"],
            "root_dir": self.serverapp.root_dir,
            "dask_client_future": self.settings["dask_client_future"],
            "model_parameters": self.settings["model_parameters"],
            "preferred_dir": self.serverapp.contents_manager.preferred_dir,
            "chat_handlers": self.settings["jai_chat_handlers"],
            "context_providers": self.settings["jai_context_providers"],
        }
        context_providers_clses = [
            FileContextProvider,
        ]
        for context_provider_ep in context_providers_eps:
            try:
                context_provider = context_provider_ep.load()
            except Exception as err:
                self.log.error(
                    f"Unable to load context provider class from entry point `{context_provider_ep.name}`: "
                    + f"Unexpected {err=}, {type(err)=}"
                )
                continue
            context_providers_clses.append(context_provider)

        for context_provider in context_providers_clses:
            if not issubclass(context_provider, BaseCommandContextProvider):
                self.log.error(
                    f"Unable to register context provider `{context_provider.id}` because it does not inherit from `BaseCommandContextProvider`"
                )
                continue

            if context_provider.id in context_providers:
                self.log.error(
                    f"Unable to register context provider `{context_provider.id}` because it already exists"
                )
                continue

            if not re.match(r"^[a-zA-Z0-9_]+$", context_provider.id):
                self.log.error(
                    f"Context provider `{context_provider.id}` is an invalid ID; "
                    + f"must contain only letters, numbers, and underscores"
                )
                continue

            context_providers[context_provider.id] = context_provider(
                **context_providers_kwargs
            )
            self.log.info(f"Registered context provider `{context_provider.id}`.")
