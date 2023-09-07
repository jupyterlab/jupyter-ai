import json
import logging
import os
import shutil
import time
from typing import Optional, Union

from deepmerge import always_merger as Merger
from jsonschema import Draft202012Validator as Validator
from jupyter_ai.models import DescribeConfigResponse, GlobalConfig, UpdateConfigRequest
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


def _validate_provider_authn(config: GlobalConfig, provider: AnyProvider):
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

    def __init__(
        self,
        log: Logger,
        lm_providers: LmProvidersDict,
        em_providers: EmProvidersDict,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.log = log
        """List of LM providers."""
        self._lm_providers = lm_providers
        """List of EM providers."""
        self._em_providers = em_providers

        """When the server last read the config file. If the file was not
        modified after this time, then we can return the cached
        `self._config`."""
        self._last_read: Optional[int] = None

        """In-memory cache of the `GlobalConfig` object parsed from the config
        file."""
        self._config: Optional[GlobalConfig] = None

        self._init_config_schema()
        self._init_validator()
        self._init_config()

    def _init_config_schema(self):
        if not os.path.exists(self.schema_path):
            os.makedirs(os.path.dirname(self.schema_path), exist_ok=True)
            shutil.copy(OUR_SCHEMA_PATH, self.schema_path)

    def _init_validator(self) -> Validator:
        with open(OUR_SCHEMA_PATH, encoding="utf-8") as f:
            schema = json.loads(f.read())
            Validator.check_schema(schema)
            self.validator = Validator(schema)

    def _init_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, encoding="utf-8") as f:
                config = GlobalConfig(**json.loads(f.read()))
                # re-write to the file to validate the config and apply any
                # updates to the config file immediately
                self._write_config(config)
            return

        properties = self.validator.schema.get("properties", {})
        field_list = GlobalConfig.__fields__.keys()
        field_dict = {
            field: properties.get(field).get("default") for field in field_list
        }
        default_config = GlobalConfig(**field_dict)
        self._write_config(default_config)

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
            if not lm_provider:
                raise ValueError(
                    f"No language model is associated with '{config.model_provider_id}'."
                )
            _validate_provider_authn(config, lm_provider)

        # validate embedding model config
        if config.embeddings_provider_id:
            _, em_provider = get_em_provider(
                config.embeddings_provider_id, self._em_providers
            )
            if not em_provider:
                raise ValueError(
                    f"No embedding model is associated with '{config.embeddings_provider_id}'."
                )
            _validate_provider_authn(config, em_provider)

    def _write_config(self, new_config: GlobalConfig):
        """Updates configuration and persists it to disk. This accepts a
        complete `GlobalConfig` object, and should not be called publicly."""
        # remove any empty field dictionaries
        new_config.fields = {k: v for k, v in new_config.fields.items() if v}

        self._validate_config(new_config)
        with open(self.config_path, "w") as f:
            json.dump(new_config.dict(), f, indent=self.indentation_depth)

    def delete_api_key(self, key_name: str):
        config_dict = self._read_config().dict()
        lm_provider = self.lm_provider
        em_provider = self.em_provider
        required_keys = []
        if (
            lm_provider
            and lm_provider.auth_strategy
            and lm_provider.auth_strategy.type == "env"
        ):
            required_keys.append(lm_provider.auth_strategy.name)
        if (
            em_provider
            and em_provider.auth_strategy
            and em_provider.auth_strategy.type == "env"
        ):
            required_keys.append(self.em_provider.auth_strategy.name)

        if key_name in required_keys:
            raise KeyInUseError(
                "This API key is currently in use by the language or embedding model. Please change the model before deleting the corresponding API key."
            )

        config_dict["api_keys"].pop(key_name, None)
        self._write_config(GlobalConfig(**config_dict))

    def update_config(self, config_update: UpdateConfigRequest):
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
        config = self._read_config()
        lm_gid = config.model_provider_id
        if lm_gid is None:
            return None

        _, Provider = get_lm_provider(config.model_provider_id, self._lm_providers)
        return Provider

    @property
    def em_provider(self):
        config = self._read_config()
        em_gid = config.embeddings_provider_id
        if em_gid is None:
            return None

        _, Provider = get_em_provider(em_gid, self._em_providers)
        return Provider

    @property
    def lm_provider_params(self):
        # get generic fields
        config = self._read_config()
        lm_gid = config.model_provider_id
        if not lm_gid:
            return None

        lm_lid = lm_gid.split(":", 1)[1]
        fields = config.fields.get(lm_gid, {})

        # get authn fields
        _, Provider = get_lm_provider(lm_gid, self._lm_providers)
        authn_fields = {}
        if Provider.auth_strategy and Provider.auth_strategy.type == "env":
            key_name = Provider.auth_strategy.name
            authn_fields[key_name.lower()] = config.api_keys[key_name]

        return {
            "model_id": lm_lid,
            **fields,
            **authn_fields,
        }

    @property
    def em_provider_params(self):
        # get generic fields
        config = self._read_config()
        em_gid = config.embeddings_provider_id
        if not em_gid:
            return None

        em_lid = em_gid.split(":", 1)[1]

        # get authn fields
        _, Provider = get_em_provider(em_gid, self._em_providers)
        authn_fields = {}
        if Provider.auth_strategy and Provider.auth_strategy.type == "env":
            key_name = Provider.auth_strategy.name
            authn_fields[key_name.lower()] = config.api_keys[key_name]

        return {
            "model_id": em_lid,
            **authn_fields,
        }
