import json
import logging
import os
import shutil
import time
from typing import List, Optional, Type, Union

from deepmerge import always_merger as Merger
from jsonschema import Draft202012Validator as Validator
from jupyter_ai.models import DescribeConfigResponse, GlobalConfig, UpdateConfigRequest
from jupyter_ai_magics import JupyternautPersona, Persona
from jupyter_ai_magics.utils import (
    AnyProvider,
    EmProvidersDict,
    LmProvidersDict,
    get_em_provider,
    get_lm_provider,
)
from jupyter_core.paths import jupyter_data_dir
from traitlets import Integer, Unicode
from traitlets.config import Configurable

Logger = Union[logging.Logger, logging.LoggerAdapter]

# default path to config
DEFAULT_CONFIG_PATH = os.path.join(jupyter_data_dir(), "jupyter_ai", "config.json")

# default path to config JSON Schema
DEFAULT_SCHEMA_PATH = os.path.join(
    jupyter_data_dir(), "jupyter_ai", "config_schema.json"
)

# default no. of spaces to use when formatting config
DEFAULT_INDENTATION_DEPTH = 4

# path to the default schema defined in this project
# if a file does not exist at SCHEMA_PATH, this file is used as a default.
OUR_SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "config", "config_schema.json"
)


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


def _validate_provider_authn(config: GlobalConfig, provider: Type[AnyProvider]):
    # TODO: handle non-env auth strategies
    if not provider.auth_strategy or provider.auth_strategy.type != "env":
        return

    if provider.auth_strategy.name not in config.api_keys:
        raise AuthError(
            f"Missing API key for '{provider.auth_strategy.name}' in the config."
        )


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

    schema_path = Unicode(
        default_value=DEFAULT_SCHEMA_PATH,
        help="Path to the configuration's corresponding JSON Schema file.",
        allow_none=False,
        config=True,
    )

    indentation_depth = Integer(
        default_value=DEFAULT_INDENTATION_DEPTH,
        help="Indentation depth, in number of spaces per level.",
        allow_none=False,
        config=True,
    )

    model_provider_id: Optional[str]
    embeddings_provider_id: Optional[str]
    completions_model_provider_id: Optional[str]

    def __init__(
        self,
        log: Logger,
        lm_providers: LmProvidersDict,
        em_providers: EmProvidersDict,
        allowed_providers: Optional[List[str]],
        blocked_providers: Optional[List[str]],
        allowed_models: Optional[List[str]],
        blocked_models: Optional[List[str]],
        defaults: dict,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.log = log

        self._lm_providers = lm_providers
        """List of LM providers."""
        self._em_providers = em_providers
        """List of EM providers."""

        self._allowed_providers = allowed_providers
        self._blocked_providers = blocked_providers
        self._allowed_models = allowed_models
        self._blocked_models = blocked_models
        self._defaults = defaults
        """Provider defaults."""

        self._last_read: Optional[int] = None
        """When the server last read the config file. If the file was not
        modified after this time, then we can return the cached
        `self._config`."""

        self._config: Optional[GlobalConfig] = None
        """In-memory cache of the `GlobalConfig` object parsed from the config
        file."""

        self._init_config_schema()
        self._init_validator()
        self._init_config()

    def _init_config_schema(self):
        if not os.path.exists(self.schema_path):
            os.makedirs(os.path.dirname(self.schema_path), exist_ok=True)
            shutil.copy(OUR_SCHEMA_PATH, self.schema_path)

    def _init_validator(self) -> None:
        with open(OUR_SCHEMA_PATH, encoding="utf-8") as f:
            schema = json.loads(f.read())
            Validator.check_schema(schema)
            self.validator = Validator(schema)

    def _init_config(self):
        default_config = self._init_defaults()
        if os.path.exists(self.config_path):
            self._process_existing_config(default_config)
        else:
            self._create_default_config(default_config)

    def _process_existing_config(self, default_config):
        with open(self.config_path, encoding="utf-8") as f:
            existing_config = json.loads(f.read())
            merged_config = Merger.merge(
                default_config,
                {k: v for k, v in existing_config.items() if v is not None},
            )
            config = GlobalConfig(**merged_config)
            validated_config = self._validate_model_ids(config)

            # re-write to the file to validate the config and apply any
            # updates to the config file immediately
            self._write_config(validated_config)

    def _validate_model_ids(self, config):
        lm_provider_keys = ["model_provider_id", "completions_model_provider_id"]
        em_provider_keys = ["embeddings_provider_id"]

        # if the currently selected language or embedding model are
        # forbidden, set them to `None` and log a warning.
        for lm_key in lm_provider_keys:
            lm_id = getattr(config, lm_key)
            if lm_id is not None and not self._validate_model(lm_id, raise_exc=False):
                self.log.warning(
                    f"Language model {lm_id} is forbidden by current allow/blocklists. Setting to None."
                )
                setattr(config, lm_key, None)
        for em_key in em_provider_keys:
            em_id = getattr(config, em_key)
            if em_id is not None and not self._validate_model(em_id, raise_exc=False):
                self.log.warning(
                    f"Embedding model {em_id} is forbidden by current allow/blocklists. Setting to None."
                )
                setattr(config, em_key, None)

        # if the currently selected language or embedding model ids are
        # not associated with models, set them to `None` and log a warning.
        for lm_key in lm_provider_keys:
            lm_id = getattr(config, lm_key)
            if lm_id is not None and not get_lm_provider(lm_id, self._lm_providers)[1]:
                self.log.warning(
                    f"No language model is associated with '{lm_id}'. Setting to None."
                )
                setattr(config, lm_key, None)
        for em_key in em_provider_keys:
            em_id = getattr(config, em_key)
            if em_id is not None and not get_em_provider(em_id, self._em_providers)[1]:
                self.log.warning(
                    f"No embedding model is associated with '{em_id}'. Setting to None."
                )
                setattr(config, em_key, None)

        return config

    def _create_default_config(self, default_config):
        self._write_config(GlobalConfig(**default_config))

    def _init_defaults(self):
        field_list = GlobalConfig.__fields__.keys()
        properties = self.validator.schema.get("properties", {})
        field_dict = {
            field: properties.get(field).get("default") for field in field_list
        }
        if self._defaults is None:
            return field_dict

        for field in field_list:
            default_value = self._defaults.get(field)
            if default_value is not None:
                field_dict[field] = default_value
        return field_dict

    def _read_config(self) -> GlobalConfig:
        """Returns the user's current configuration as a GlobalConfig object.
        This should never be sent to the client as it includes API keys. Prefer
        self.get_config() for sending the config to the client."""
        if self._config and self._last_read:
            last_write = os.stat(self.config_path).st_mtime_ns
            if last_write <= self._last_read:
                return self._config

        with open(self.config_path, encoding="utf-8") as f:
            self._last_read = time.time_ns()
            raw_config = json.loads(f.read())
            config = GlobalConfig(**raw_config)
            self._validate_config(config)
            return config

    def _validate_config(self, config: GlobalConfig):
        """Method used to validate the configuration. This is called after every
        read and before every write to the config file. Guarantees that the
        config file conforms to the JSON Schema, and that the language and
        embedding models have authn credentials if specified."""
        self.validator.validate(config.dict())

        # validate language model config
        if config.model_provider_id:
            _, lm_provider = get_lm_provider(
                config.model_provider_id, self._lm_providers
            )

            # verify model is declared by some provider
            if not lm_provider:
                raise ValueError(
                    f"No language model is associated with '{config.model_provider_id}'."
                )

            # verify model is not blocked
            self._validate_model(config.model_provider_id)

            # verify model is authenticated
            _validate_provider_authn(config, lm_provider)

        # validate embedding model config
        if config.embeddings_provider_id:
            _, em_provider = get_em_provider(
                config.embeddings_provider_id, self._em_providers
            )

            # verify model is declared by some provider
            if not em_provider:
                raise ValueError(
                    f"No embedding model is associated with '{config.embeddings_provider_id}'."
                )

            # verify model is not blocked
            self._validate_model(config.embeddings_provider_id)

            # verify model is authenticated
            _validate_provider_authn(config, em_provider)

    def _validate_model(self, model_id: str, raise_exc=True):
        """
        Validates a model against the set of allow/blocklists specified by the
        traitlets configuration, returning `True` if the model is allowed, and
        raising a `BlockedModelError` otherwise. If `raise_exc=False`, this
        function returns `False` if the model is not allowed.
        """

        assert model_id is not None
        components = model_id.split(":", 1)
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

            if self._allowed_models and model_id not in self._allowed_models:
                raise BlockedModelError("Model not included in the model allowlist.")

            if self._blocked_models and model_id in self._blocked_models:
                raise BlockedModelError("Model included in the model blocklist.")
        except BlockedModelError as e:
            if raise_exc:
                raise e
            else:
                return False

        return True

    def _write_config(self, new_config: GlobalConfig):
        """Updates configuration and persists it to disk. This accepts a
        complete `GlobalConfig` object, and should not be called publicly."""
        # remove any empty field dictionaries
        new_config.fields = {k: v for k, v in new_config.fields.items() if v}
        new_config.completions_fields = {
            k: v for k, v in new_config.completions_fields.items() if v
        }

        self._validate_config(new_config)
        with open(self.config_path, "w") as f:
            json.dump(new_config.dict(), f, indent=self.indentation_depth)

    def delete_api_key(self, key_name: str):
        config_dict = self._read_config().dict()
        required_keys = []
        for provider in [
            self.lm_provider,
            self.em_provider,
            self.completions_lm_provider,
        ]:
            if (
                provider
                and provider.auth_strategy
                and provider.auth_strategy.type == "env"
            ):
                required_keys.append(provider.auth_strategy.name)

        if key_name in required_keys:
            raise KeyInUseError(
                "This API key is currently in use by the language or embedding model. Please change the model before deleting the corresponding API key."
            )

        config_dict["api_keys"].pop(key_name, None)
        self._write_config(GlobalConfig(**config_dict))

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

        config_dict = self._read_config().dict()
        Merger.merge(config_dict, config_update.dict(exclude_unset=True))
        self._write_config(GlobalConfig(**config_dict))

    # this cannot be a property, as the parent Configurable already defines the
    # self.config attr.
    def get_config(self):
        config = self._read_config()
        config_dict = config.dict(exclude_unset=True)
        api_key_names = list(config_dict.pop("api_keys").keys())
        return DescribeConfigResponse(
            **config_dict, api_keys=api_key_names, last_read=self._last_read
        )

    @property
    def lm_gid(self):
        config = self._read_config()
        return config.model_provider_id

    @property
    def em_gid(self):
        config = self._read_config()
        return config.embeddings_provider_id

    @property
    def lm_provider(self):
        return self._get_provider("model_provider_id", self._lm_providers)

    @property
    def em_provider(self):
        return self._get_provider("embeddings_provider_id", self._em_providers)

    @property
    def completions_lm_provider(self):
        return self._get_provider("completions_model_provider_id", self._lm_providers)

    def _get_provider(self, key, listing):
        config = self._read_config()
        gid = getattr(config, key)
        if gid is None:
            return None

        _, Provider = get_lm_provider(gid, listing)
        return Provider

    @property
    def lm_provider_params(self):
        return self._provider_params("model_provider_id", self._lm_providers)

    @property
    def em_provider_params(self):
        return self._provider_params("embeddings_provider_id", self._em_providers)

    @property
    def completions_lm_provider_params(self):
        return self._provider_params(
            "completions_model_provider_id", self._lm_providers
        )

    def _provider_params(self, key, listing):
        # get generic fields
        config = self._read_config()
        gid = getattr(config, key)
        if not gid:
            return None

        lid = gid.split(":", 1)[1]

        # get authn fields
        _, Provider = get_em_provider(gid, listing)
        authn_fields = {}
        if Provider.auth_strategy and Provider.auth_strategy.type == "env":
            keyword_param = (
                Provider.auth_strategy.keyword_param
                or Provider.auth_strategy.name.lower()
            )
            key_name = Provider.auth_strategy.name
            authn_fields[keyword_param] = config.api_keys[key_name]

        return {
            "model_id": lid,
            **authn_fields,
        }

    @property
    def persona(self) -> Persona:
        """
        The current agent persona, set by the selected LM provider. If the
        selected LM provider is `None`, this property returns
        `JupyternautPersona` by default.
        """
        lm_provider = self.lm_provider
        persona = getattr(lm_provider, "persona", None) or JupyternautPersona
        return persona
