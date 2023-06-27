import json
import logging
import os
from typing import Any, Dict, Union

from jupyter_ai.models import GlobalConfig
from jupyter_ai_magics.utils import (
    AnyProvider,
    EmProvidersDict,
    LmProvidersDict,
    get_em_provider,
    get_lm_provider,
)
from jupyter_core.paths import jupyter_data_dir

Logger = Union[logging.Logger, logging.LoggerAdapter]


class ConfigManager:
    """Provides model and embedding provider id along
    with the credentials to authenticate providers.
    """

    def __init__(
        self, log: Logger, lm_providers: LmProvidersDict, em_providers: EmProvidersDict
    ):
        self.log = log
        self.save_dir = os.path.join(jupyter_data_dir(), "jupyter_ai")
        self.save_path = os.path.join(self.save_dir, "config.json")
        self.config = None
        self.lm_providers = lm_providers
        self.em_providers = em_providers
        self.lm_provider = None
        self.lm_provider_params = {}
        self.em_provider = None
        self.em_provider_params = {}
        self._load()

    def update(self, config: GlobalConfig, save_to_disk: bool = True):
        self._update_lm_provider(config)
        self._update_em_provider(config)
        if save_to_disk:
            self._save(config)
        self.config = config

    def get_config(self):
        return self.config

    def get_lm_provider(self):
        return self.lm_provider

    def get_lm_provider_params(self):
        return self.lm_provider_params

    def get_em_provider(self):
        return self.em_provider

    def get_em_provider_params(self):
        return self.em_provider_params

    def _authenticate_provider(
        self,
        provider: AnyProvider,
        provider_params: Dict[str, Any],
        config: GlobalConfig,
    ):
        auth_strategy = provider.auth_strategy
        if auth_strategy and auth_strategy.type == "env":
            api_keys = config.api_keys
            name = auth_strategy.name
            if name not in api_keys:
                raise ValueError(
                    f"Missing value for '{auth_strategy.name}' in the config."
                )
            provider_params[name.lower()] = api_keys[name]

    def _update_lm_provider(self, config: GlobalConfig):
        model_id = config.model_provider_id

        if not model_id:
            self.lm_provider = None
            self.lm_provider_params = None
            return

        local_model_id, provider = get_lm_provider(model_id, self.lm_providers)

        if not provider:
            raise ValueError(f"No provider and model found with '{model_id}'")

        fields = config.fields.get(model_id, {})
        provider_params = {"model_id": local_model_id, **fields}

        self._authenticate_provider(provider, provider_params, config)
        self.lm_provider = provider
        self.lm_provider_params = provider_params

    def _update_em_provider(self, config: GlobalConfig):
        model_id = config.embeddings_provider_id

        if not model_id:
            self.em_provider = None
            self.em_provider_params
            return

        local_model_id, provider = get_em_provider(model_id, self.em_providers)

        if not provider:
            raise ValueError(f"No provider and model found with '{model_id}'")

        provider_params = {"model_id": local_model_id}

        self._authenticate_provider(provider, provider_params, config)
        self.em_provider = provider
        self.em_provider_params = provider_params

    def _save(self, config: GlobalConfig):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        with open(self.save_path, "w") as f:
            f.write(config.json())

    def _load(self):
        if os.path.exists(self.save_path):
            with open(self.save_path, encoding="utf-8") as f:
                config = GlobalConfig(**json.loads(f.read()))
                self.update(config, False)
            return

        # otherwise, create a new empty config file
        self.update(GlobalConfig(), True)
