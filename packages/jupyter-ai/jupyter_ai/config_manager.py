import json
import logging
import os
import time
from copy import deepcopy
from typing import Any, Optional, Union

from deepmerge import always_merger
from jupyter_core.paths import jupyter_data_dir
from traitlets import Integer, Unicode
from traitlets.config import Configurable

from .config import DescribeConfigResponse, JaiConfig, UpdateConfigRequest

Logger = Union[logging.Logger, logging.LoggerAdapter]

# default path to config
DEFAULT_CONFIG_PATH = os.path.join(jupyter_data_dir(), "jupyter_ai", "config.json")

# default no. of spaces to use when formatting config
DEFAULT_INDENTATION_DEPTH = 4


class AuthError(Exception):
    pass


class WriteConflictError(Exception):
    pass


class KeyInUseError(Exception):
    pass


class KeyEmptyError(Exception):
    pass


class BlockedModelError(Exception):
    pass


def remove_none_entries(d: dict):
    """
    Returns a deep copy of the given dictionary that excludes all top-level
    entries whose value is `None`.
    """
    d = {k: deepcopy(d[k]) for k in d if d[k] is not None}
    return d


class ConfigManager(Configurable):
    """Provides model and embedding provider id along
    with the credentials to authenticate providers.
    """

    config_path = Unicode(
        default_value=DEFAULT_CONFIG_PATH,
        help="Path to the configuration file.",
        allow_none=False,
        config=True,
    )

    indentation_depth = Integer(
        default_value=DEFAULT_INDENTATION_DEPTH,
        help="Indentation depth, in number of spaces per level.",
        allow_none=False,
        config=True,
    )

    model_provider_id: Optional[str] = None
    embeddings_provider_id: Optional[str] = None
    completions_model_provider_id: Optional[str] = None

    _defaults: dict
    """
    Dictionary that maps config keys (e.g. `model_provider_id`, `fields`) to
    user-specified overrides, set by traitlets configuration.

    Values in this dictionary should never be mutated as they may refer to
    entries in the global `self.settings` dictionary.
    """

    _last_read: Optional[int]
    """
    When the server last read the config file. If the file was not
    modified after this time, then we can return the cached
    `self._config`.
    """

    def __init__(
        self,
        log: Logger,
        defaults: dict,
        allowed_providers: Optional[list[str]] = None,
        blocked_providers: Optional[list[str]] = None,
        allowed_models: Optional[list[str]] = None,
        blocked_models: Optional[list[str]] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.log = log

        self._allowed_providers = allowed_providers
        self._blocked_providers = blocked_providers
        self._allowed_models = allowed_models
        self._blocked_models = blocked_models

        self._lm_providers: dict[str, Any] = (
            {}
        )  # Placeholder: should be set to actual language model providers
        self._defaults = remove_none_entries(defaults)
        self._last_read: Optional[int] = None

        self._config: Optional[JaiConfig] = None
        """The `JaiConfig` object that represents the config file."""

        self._init_config()

    def _init_config(self):
        """
        Initializes the config from the existing config file. If a config file
        does not exist, then a default one is created. If any field was set in
        the `defaults` argument passed to the constructor, they will take
        precedence over the existing configuration.

        TODO: how to handle invalid config files? create a copy & replace it
        with an empty default?
        """
        # If config file exists, validate it first
        if os.path.exists(self.config_path) and os.stat(self.config_path).st_size != 0:
            self._process_existing_config()
        else:
            # Otherwise, write the default config to the config path
            self._write_config(JaiConfig())

        # Allow fields specified in `defaults` argument to override the local
        # configuration on init.
        if self._defaults:
            existing_config_args = self._read_config().model_dump()
            merged_config_args = always_merger.merge(
                existing_config_args, self._defaults
            )
            merged_config = JaiConfig(**merged_config_args)
            self._write_config(merged_config)

    def _process_existing_config(self):
        """
        Reads the existing configuration file and validates it.
        """
        with open(self.config_path, encoding="utf-8") as f:
            existing_config = json.loads(f.read())
            config = JaiConfig(**existing_config)

        # re-write to the file to validate the config and apply any
        # updates to the config file immediately
        self._write_config(config)

    def _read_config(self) -> JaiConfig:
        """
        Returns the user's current configuration as a `JaiConfig` object.

        NOTE: This method is private because the returned object should never be
        sent to the client as it includes API keys. Prefer self.get_config() for
        sending the config to the client.
        """
        if self._config and self._last_read:
            last_write = os.stat(self.config_path).st_mtime_ns
            if last_write <= self._last_read:
                return self._config

        with open(self.config_path, encoding="utf-8") as f:
            self._last_read = time.time_ns()
            raw_config = json.loads(f.read())
            if "embeddings_fields" not in raw_config:
                raw_config["embeddings_fields"] = {}
            config = JaiConfig(**raw_config)
            self._validate_config(config)
            return config

    def _validate_config(self, config: JaiConfig):
        """
        Method used to validate the configuration. This is called after every
        read and before every write to the config file. Guarantees that the
        user has specified authentication for all configured models that require
        it.
        """
        # TODO: re-implement this w/ liteLLM
        # validate language model config
        # if config.model_provider_id:
        #     _, lm_provider = get_lm_provider(
        #         config.model_provider_id, self._lm_providers
        #     )

        #     # verify model is declared by some provider
        #     if not lm_provider:
        #         raise ValueError(
        #             f"No language model is associated with '{config.model_provider_id}'."
        #         )

        #     # verify model is not blocked
        #     self._validate_model(config.model_provider_id)

        #     # verify model is authenticated
        #     _validate_provider_authn(config, lm_provider)

        #     # verify fields exist for this model if needed
        #     if lm_provider.fields and config.model_provider_id not in config.fields:
        #         config.fields[config.model_provider_id] = {}

        # validate completions model config
        # if config.completions_model_provider_id:
        #     _, completions_provider = get_lm_provider(
        #         config.completions_model_provider_id, self._lm_providers
        #     )

        #     # verify model is declared by some provider
        #     if not completions_provider:
        #         raise ValueError(
        #             f"No language model is associated with '{config.completions_model_provider_id}'."
        #         )

        #     # verify model is not blocked
        #     self._validate_model(config.completions_model_provider_id)

        #     # verify model is authenticated
        #     _validate_provider_authn(config, completions_provider)

        #     # verify completions fields exist for this model if needed
        #     if (
        #         completions_provider.fields
        #         and config.completions_model_provider_id
        #         not in config.completions_fields
        #     ):
        #         config.completions_fields[config.completions_model_provider_id] = {}

        # # validate embedding model config
        # if config.embeddings_provider_id:
        #     _, em_provider = get_em_provider(
        #         config.embeddings_provider_id, self._em_providers
        #     )

        #     # verify model is declared by some provider
        #     if not em_provider:
        #         raise ValueError(
        #             f"No embedding model is associated with '{config.embeddings_provider_id}'."
        #         )

        #     # verify model is not blocked
        #     self._validate_model(config.embeddings_provider_id)

        #     # verify model is authenticated
        #     _validate_provider_authn(config, em_provider)

        #     # verify embedding fields exist for this model if needed
        #     if (
        #         em_provider.fields
        #         and config.embeddings_provider_id not in config.embeddings_fields
        #     ):
        #         config.embeddings_fields[config.embeddings_provider_id] = {}
        return

    def _validate_model(self, model_id: str, raise_exc=True):
        """
        Validates a model against the set of allow/blocklists specified by the
        traitlets configuration, returning `True` if the model is allowed, and
        raising a `BlockedModelError` otherwise. If `raise_exc=False`, this
        function returns `False` if the model is not allowed.
        """

        assert model_id is not None
        components = model_id.split("/", 1)
        assert len(components) == 2
        provider_id, _ = components

        try:
            if self._allowed_providers and provider_id not in self._allowed_providers:
                raise BlockedModelError(
                    "Model provider not included in the provider allowlist."
                )

            if self._blocked_providers and provider_id in self._blocked_providers:
                raise BlockedModelError(
                    "Model provider included in the provider blocklist."
                )

            if (
                self._allowed_models is not None
                and model_id not in self._allowed_models
            ):
                raise BlockedModelError("Model not included in the model allowlist.")

            if self._blocked_models is not None and model_id in self._blocked_models:
                raise BlockedModelError("Model included in the model blocklist.")
        except BlockedModelError as e:
            if raise_exc:
                raise e
            else:
                return False

        return True

    def _write_config(self, new_config: JaiConfig):
        """
        Updates configuration given a complete `JaiConfig` object and saves it
        to disk.
        """
        # remove any empty field dictionaries
        new_config.fields = {k: v for k, v in new_config.fields.items() if v}
        new_config.completions_fields = {
            k: v for k, v in new_config.completions_fields.items() if v
        }
        new_config.embeddings_fields = {
            k: v for k, v in new_config.embeddings_fields.items() if v
        }

        self._validate_config(new_config)
        with open(self.config_path, "w") as f:
            json.dump(new_config.model_dump(), f, indent=self.indentation_depth)

    def update_config(self, config_update: UpdateConfigRequest):  # type:ignore
        last_write = os.stat(self.config_path).st_mtime_ns
        if config_update.last_read and config_update.last_read < last_write:
            raise WriteConflictError(
                "Configuration was modified after it was read from disk."
            )

        if config_update.api_keys:
            for api_key_value in config_update.api_keys.values():
                if not api_key_value:
                    raise KeyEmptyError("API key value cannot be empty.")

        config_dict = self._read_config().model_dump()
        always_merger.merge(config_dict, config_update.model_dump(exclude_unset=True))
        self._write_config(JaiConfig(**config_dict))

    # this cannot be a property, as the parent Configurable already defines the
    # self.config attr.
    def get_config(self):
        config = self._read_config()
        config_dict = config.model_dump(exclude_unset=True)
        api_key_names = list(config_dict.pop("api_keys").keys())
        return DescribeConfigResponse(
            **config_dict, api_keys=api_key_names, last_read=self._last_read
        )

    @property
    def chat_model(self) -> str | None:
        """
        Returns the model ID of the chat model from AI settings, if any.
        """
        config = self._read_config()
        return config.model_provider_id

    @property
    def chat_model_params(self) -> dict[str, Any]:
        return self._provider_params("model_provider_id", self._lm_providers)

    def _provider_params(
        self, provider_id_attr: str, providers: dict
    ) -> dict[str, Any]:
        """
        Returns the parameters for the provider specified by the given attribute.
        """
        config = self._read_config()
        provider_id = getattr(config, provider_id_attr, None)
        if not provider_id or provider_id not in providers:
            return {}
        return providers[provider_id].get("params", {})
        return self._provider_params("model_provider_id", self._lm_providers)

    @property
    def embedding_model(self) -> str | None:
        """
        Returns the model ID of the embedding model from AI settings, if any.
        """
        config = self._read_config()
        return config.embeddings_provider_id

    @property
    def embedding_model_params(self) -> dict[str, Any]:
        # TODO
        return {}

    @property
    def completion_model(self) -> str | None:
        """
        Returns the model ID of the completion model from AI settings, if any.
        """
        config = self._read_config()
        return config.completions_model_provider_id

    @property
    def completion_model_params(self):
        # TODO
        return {}

    def delete_api_key(self, key_name: str):
        # TODO: store in .env files
        pass
