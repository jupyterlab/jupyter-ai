import json
import logging
import os
import time
from copy import deepcopy
from typing import Optional, Union

from deepmerge import Merger, always_merger
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


def _validate_provider_authn(config: GlobalConfig, provider: type[AnyProvider]):
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

    model_provider_id: Optional[str] = None
    embeddings_provider_id: Optional[str] = None
    completions_model_provider_id: Optional[str] = None

    def __init__(
        self,
        log: Logger,
        lm_providers: LmProvidersDict,
        em_providers: EmProvidersDict,
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

        self._lm_providers = lm_providers
        """List of LM providers."""
        self._em_providers = em_providers
        """List of EM providers."""

        self._allowed_providers = allowed_providers
        self._blocked_providers = blocked_providers
        self._allowed_models = allowed_models
        self._blocked_models = blocked_models
        self._defaults = defaults
        """
        Dictionary that maps config keys (e.g. `model_provider_id`, `fields`) to
        user-specified overrides, set by traitlets configuration.

        Values in this dictionary should never be mutated as they may refer to
        entries in the global `self.settings` dictionary.
        """

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
        """
        Initializes `config_schema.json` in the user's data dir whenever the
        server extension starts. Users may add custom fields to their config
        schema to insert new keys into the Jupyter AI config.

        New in v2.31.1: Jupyter AI now merges the user's existing config schema
        with Jupyter AI's config schema on init. This prevents validation errors
        on missing keys when users upgrade Jupyter AI from an older version.

        TODO v3: Remove the ability for users to provide a custom config schema.
        This feature is entirely unused as far as I am aware, and we need to
        simplify how Jupyter AI handles user configuration in v3 anyways.
        """

        # ensure the parent directory has been created
        os.makedirs(os.path.dirname(self.schema_path), exist_ok=True)

        # read existing_schema
        if os.path.exists(self.schema_path):
            with open(self.schema_path, encoding="utf-8") as f:
                existing_schema = json.load(f)
        else:
            existing_schema = {}

        # read default_schema
        with open(OUR_SCHEMA_PATH, encoding="utf-8") as f:
            default_schema = json.load(f)

        # Create a custom `deepmerge.Merger` object to merge lists using the
        # 'append_unique' strategy.
        #
        # This stops type union declarations like `["string", "null"]` from
        # growing into `["string", "null", "string", "null"]` on restart.
        # This fixes issue #1320.
        merger = Merger(
            [(list, ["append_unique"]), (dict, ["merge"]), (set, ["union"])],
            ["override"],
            ["override"],
        )

        # merge existing_schema into default_schema
        # specifying existing_schema as the second argument ensures that
        # existing_schema always overrides existing keys in default_schema, i.e.
        # this call only adds new keys in default_schema.
        schema = merger.merge(default_schema, existing_schema)
        with open(self.schema_path, encoding="utf-8", mode="w") as f:
            json.dump(schema, f, indent=self.indentation_depth)

    def _init_validator(self) -> None:
        with open(OUR_SCHEMA_PATH, encoding="utf-8") as f:
            schema = json.loads(f.read())
            Validator.check_schema(schema)
            self.validator = Validator(schema)

    def _init_config(self):
        default_config = self._init_defaults()
        if os.path.exists(self.config_path) and os.stat(self.config_path).st_size != 0:
            self._process_existing_config(default_config)
        else:
            self._create_default_config(default_config)

    def _process_existing_config(self, default_config):
        with open(self.config_path, encoding="utf-8") as f:
            existing_config = json.loads(f.read())
            if "embeddings_fields" not in existing_config:
                existing_config["embeddings_fields"] = {}
            merged_config = always_merger.merge(
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
        clm_provider_keys = ["completions_model_provider_id"]

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
        for clm_key in clm_provider_keys:
            clm_id = getattr(config, clm_key)
            if clm_id is not None and not self._validate_model(clm_id, raise_exc=False):
                self.log.warning(
                    f"Completion model {clm_id} is forbidden by current allow/blocklists. Setting to None."
                )
                setattr(config, clm_key, None)

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
        for clm_key in clm_provider_keys:
            clm_id = getattr(config, clm_key)
            if (
                clm_id is not None
                and not get_lm_provider(clm_id, self._lm_providers)[1]
            ):
                self.log.warning(
                    f"No completion model is associated with '{clm_id}'. Setting to None."
                )
                setattr(config, clm_key, None)

        return config

    def _create_default_config(self, default_config):
        self._write_config(GlobalConfig(**default_config))

    def _init_defaults(self):
        config_keys = GlobalConfig.model_fields.keys()
        schema_properties = self.validator.schema.get("properties", {})
        default_config = {
            field: schema_properties.get(field, {}).get("default")
            for field in config_keys
        }
        if self._defaults is None:
            return default_config

        for config_key in config_keys:
            # we call `deepcopy()` here to avoid directly referring to the
            # values in `self._defaults`, as they map to entries in the global
            # `self.settings` dictionary and may be mutated otherwise.
            default_value = deepcopy(self._defaults.get(config_key))
            if default_value is not None:
                default_config[config_key] = default_value
        return default_config

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
            if "embeddings_fields" not in raw_config:
                raw_config["embeddings_fields"] = {}
            config = GlobalConfig(**raw_config)
            self._validate_config(config)
            return config

    def _validate_config(self, config: GlobalConfig):
        """Method used to validate the configuration. This is called after every
        read and before every write to the config file. Guarantees that the
        config file conforms to the JSON Schema, and that the language and
        embedding models have authn credentials if specified."""
        self.validator.validate(config.model_dump())

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

            # verify fields exist for this model if needed
            if lm_provider.fields and config.model_provider_id not in config.fields:
                config.fields[config.model_provider_id] = {}

        # validate completions model config
        if config.completions_model_provider_id:
            _, completions_provider = get_lm_provider(
                config.completions_model_provider_id, self._lm_providers
            )

            # verify model is declared by some provider
            if not completions_provider:
                raise ValueError(
                    f"No language model is associated with '{config.completions_model_provider_id}'."
                )

            # verify model is not blocked
            self._validate_model(config.completions_model_provider_id)

            # verify model is authenticated
            _validate_provider_authn(config, completions_provider)

            # verify completions fields exist for this model if needed
            if (
                completions_provider.fields
                and config.completions_model_provider_id
                not in config.completions_fields
            ):
                config.completions_fields[config.completions_model_provider_id] = {}

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

            # verify embedding fields exist for this model if needed
            if (
                em_provider.fields
                and config.embeddings_provider_id not in config.embeddings_fields
            ):
                config.embeddings_fields[config.embeddings_provider_id] = {}

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

    def _write_config(self, new_config: GlobalConfig):
        """Updates configuration and persists it to disk. This accepts a
        complete `GlobalConfig` object, and should not be called publicly."""
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

    def delete_api_key(self, key_name: str):
        config_dict = self._read_config().model_dump()
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

        config_dict = self._read_config().model_dump()
        always_merger.merge(config_dict, config_update.model_dump(exclude_unset=True))
        self._write_config(GlobalConfig(**config_dict))

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
            "completions_model_provider_id", self._lm_providers, completions=True
        )

    def _provider_params(self, key, listing, completions: bool = False):
        # read config
        config = self._read_config()

        # get model ID (without provider ID component) from model universal ID
        # (with provider component).
        model_uid = getattr(config, key)
        if not model_uid:
            return None
        model_id = model_uid.split(":", 1)[1]

        # get config fields (e.g. base API URL, etc.)
        if completions:
            fields = config.completions_fields.get(model_uid, {})
        elif key == "embeddings_provider_id":
            fields = config.embeddings_fields.get(model_uid, {})
        else:
            fields = config.fields.get(model_uid, {})

        # exclude empty fields
        # TODO: modify the config manager to never save empty fields in the
        # first place.
        fields = {
            k: None if isinstance(v, str) and not len(v) else v
            for k, v in fields.items()
        }

        # get authn fields
        _, Provider = (
            get_em_provider(model_uid, listing)
            if key == "embeddings_provider_id"
            else get_lm_provider(model_uid, listing)
        )
        authn_fields = {}
        if Provider.auth_strategy and Provider.auth_strategy.type == "env":
            keyword_param = (
                Provider.auth_strategy.keyword_param
                or Provider.auth_strategy.name.lower()
            )
            key_name = Provider.auth_strategy.name
            authn_fields[keyword_param] = config.api_keys[key_name]

        return {
            "model_id": model_id,
            **fields,
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
