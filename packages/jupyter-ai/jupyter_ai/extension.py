import os
import time
import types
from asyncio import get_event_loop_policy
from functools import partial
from typing import TYPE_CHECKING, Optional

import traitlets
from jupyter_ai_magics import BaseProvider, JupyternautPersona
from jupyter_ai_magics.utils import get_em_providers, get_lm_providers
from jupyter_events import EventLogger
from jupyter_server.extension.application import ExtensionApp
from jupyter_server.serverapp import ServerApp
from jupyter_server_fileid.manager import (  # type: ignore[import-untyped]
    BaseFileIdManager,
)
from jupyterlab_chat.models import Message
from jupyterlab_chat.ychat import YChat
from pycrdt import ArrayEvent
from tornado.web import StaticFileHandler
from traitlets import Integer, List, Type, Unicode
from traitlets.config import Config

from .completions.handlers import DefaultInlineCompletionHandler
from .config_manager import ConfigManager
from .handlers import (
    ApiKeysHandler,
    EmbeddingsModelProviderHandler,
    GlobalConfigHandler,
    InterruptStreamingHandler,
    ModelProviderHandler,
)
from .personas import PersonaManager

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

from jupyter_collaboration import (  # type:ignore[import-untyped]  # isort:skip
    __version__ as jupyter_collaboration_version,
)


JUPYTERNAUT_AVATAR_ROUTE = JupyternautPersona.avatar_route
JUPYTERNAUT_AVATAR_PATH = str(
    os.path.join(os.path.dirname(__file__), "static", "jupyternaut.svg")
)

JCOLLAB_VERSION = int(jupyter_collaboration_version[0])

if JCOLLAB_VERSION >= 3:
    from jupyter_server_ydoc.utils import (  # type:ignore[import-not-found,import-untyped]
        JUPYTER_COLLABORATION_EVENTS_URI,
    )
else:
    from jupyter_collaboration.utils import (  # type:ignore[import-not-found,import-untyped]
        JUPYTER_COLLABORATION_EVENTS_URI,
    )


class AiExtension(ExtensionApp):
    name = "jupyter_ai"
    handlers = [  # type:ignore[assignment]
        (r"api/ai/api_keys/(?P<api_key_name>\w+)", ApiKeysHandler),
        (r"api/ai/config/?", GlobalConfigHandler),
        (r"api/ai/chats/stop_streaming?", InterruptStreamingHandler),
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

    persona_manager_class = Type(
        klass=PersonaManager,
        default_value=PersonaManager,
        config=True,
        help="The `PersonaManager` class.",
    )

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

    model_parameters = traitlets.Dict(
        key_trait=Unicode(),
        value_trait=traitlets.Dict(),
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

    default_completions_model = Unicode(
        default_value=None,
        allow_none=True,
        help="""
        Default completions model to use, as string in the format
        <provider-id>:<model-id>, defaults to None.
        """,
        config=True,
    )

    default_api_keys = traitlets.Dict(
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

    def initialize(self):
        super().initialize()

        self.ychats_by_room: dict[str, YChat] = {}
        """Cache of YChat instances, indexed by room ID."""

        self.event_logger = self.serverapp.web_app.settings["event_logger"]
        self.event_logger.add_listener(
            schema_id=JUPYTER_COLLABORATION_EVENTS_URI, listener=self.connect_chat
        )

    @property
    def event_loop(self) -> "AbstractEventLoop":
        """
        Returns a reference to the asyncio event loop.
        """
        return get_event_loop_policy().get_event_loop()

    async def connect_chat(
        self, logger: EventLogger, schema_id: str, data: dict
    ) -> None:
        # ignore events that are not chat room initialization events
        if not (
            data["room"].startswith("text:chat:")
            and data["action"] == "initialize"
            and data["msg"] == "Room initialized"
        ):
            return

        # log room ID
        room_id = data["room"]
        self.log.info(f"Connecting to a chat room with room ID: {room_id}.")

        # get YChat document associated with the room
        ychat = await self.get_chat(room_id)
        if ychat is None:
            return

        # initialize persona manager
        persona_manager = self._init_persona_manager(room_id, ychat)
        if not persona_manager:
            self.log.error(
                "Jupyter AI was unable to initialize its AI personas. They are not available for use in chat until this error is resolved. "
                + "Please verify your configuration and open a new issue on GitHub if this error persists."
            )
            return

        callback = partial(self.on_change, room_id, persona_manager)
        ychat.ymessages.observe(callback)

    async def get_chat(self, room_id: str) -> YChat:
        """
        Retrieves the YChat instance associated with a room ID. This method
        is cached, i.e. successive calls with the same room ID quickly return a
        cached value.
        """
        if room_id in self.ychats_by_room:
            return self.ychats_by_room[room_id]

        assert self.serverapp
        if JCOLLAB_VERSION >= 3:
            collaboration = self.serverapp.web_app.settings["jupyter_server_ydoc"]
            document = await collaboration.get_document(room_id=room_id, copy=False)
        else:
            collaboration = self.serverapp.web_app.settings["jupyter_collaboration"]
            server = collaboration.ywebsocket_server

            room = await server.get_room(room_id)
            document = room._document

        assert document
        self.ychats_by_room[room_id] = document
        return document

    def on_change(
        self, room_id: str, persona_manager: PersonaManager, events: ArrayEvent
    ) -> None:
        assert self.serverapp

        for change in events.delta:  # type:ignore[attr-defined]
            if not "insert" in change.keys():
                continue

            # the "if not m['raw_time']" clause is necessary because every new
            # message triggers 2 events, one with `raw_time` set to `True` and
            # another with `raw_time` set to `False` milliseconds later.
            # we should explore fixing this quirk in Jupyter Chat.
            #
            # Ref: https://github.com/jupyterlab/jupyter-chat/issues/212
            new_messages = [
                Message(**m) for m in change["insert"] if not m.get("raw_time", False)
            ]
            for new_message in new_messages:
                persona_manager.route_message(new_message)

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
            "completions_model_provider_id": self.default_completions_model,
            "api_keys": self.default_api_keys,
            "fields": self.model_parameters,
            "embeddings_fields": self.model_parameters,
            "completions_fields": self.model_parameters,
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

        self.settings["jai_event_loop"] = self.event_loop

        # Create empty dictionary for events communicating that
        # message generation/streaming got interrupted.
        self.settings["jai_message_interrupted"] = {}

        latency_ms = round((time.time() - start) * 1000)
        self.log.info(f"Initialized Jupyter AI server extension in {latency_ms} ms.")

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
        # TODO: explore if cleanup is necessary

    def _init_persona_manager(
        self, room_id: str, ychat: YChat
    ) -> Optional[PersonaManager]:
        """
        Initializes a `PersonaManager` instance scoped to a `YChat`.

        This method should not raise an exception. Upon encountering an
        exception, this method will catch it, log it, and return `None`.
        """
        persona_manager: Optional[PersonaManager] = None

        try:
            config_manager = self.settings.get("jai_config_manager", None)
            assert config_manager and isinstance(config_manager, ConfigManager)

            message_interrupted = self.settings.get("jai_message_interrupted", None)
            assert message_interrupted is not None and isinstance(
                message_interrupted, dict
            )

            assert self.serverapp
            assert self.serverapp.web_app
            assert self.serverapp.web_app.settings
            fileid_manager = self.serverapp.web_app.settings.get(
                "file_id_manager", None
            )
            assert isinstance(fileid_manager, BaseFileIdManager)

            contents_manager = self.serverapp.contents_manager
            root_dir = getattr(contents_manager, "root_dir", None)
            assert isinstance(root_dir, str)

            PersonaManagerClass = self.persona_manager_class
            persona_manager = PersonaManagerClass(
                parent=self,
                room_id=room_id,
                ychat=ychat,
                config_manager=config_manager,
                fileid_manager=fileid_manager,
                root_dir=root_dir,
                event_loop=self.event_loop,
                message_interrupted=message_interrupted,
            )
        except Exception as e:
            # TODO: how to stop the extension when this fails
            # also why do uncaught exceptions produce an empty error log in Jupyter Server?
            self.log.error(
                f"Unable to initialize PersonaManager in YChat with ID '{ychat.get_id()}' due to an exception printed below."
            )
            self.log.exception(e)
        finally:
            return persona_manager

    def _link_jupyter_server_extension(self, server_app: ServerApp):
        """Setup custom config needed by this extension."""
        c = Config()
        c.ContentsManager.allow_hidden = True
        c.ContentsManager.hide_globs = [
            "__pycache__",  # Python bytecode cache directories
            "*.pyc",  # Compiled Python files
            "*.pyo",  # Optimized Python files
            ".DS_Store",  # macOS system files
            "*~",  # Editor backup files
            ".ipynb_checkpoints",  # Jupyter notebook checkpoint files
            ".git",  # Git version control directory
            ".venv",  # Python virtual environment directory
            "venv",  # Python virtual environment directory
            ".env",  # Environment variable files
            "node_modules",  # Node.js dependencies directory
            ".pytest_cache",  # PyTest cache directory
            ".mypy_cache",  # MyPy type checker cache directory
            "*.egg-info",  # Python package metadata directories
        ]
        server_app.update_config(c)
        super()._link_jupyter_server_extension(server_app)
