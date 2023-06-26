import ray
from jupyter_ai.actors.base import ACTOR_TYPE, Logger
from jupyter_ai.models import GlobalConfig
from jupyter_ai_magics.utils import LmProvidersDict, get_lm_provider


@ray.remote
class ChatProviderActor:
    def __init__(self, log: Logger, lm_providers: LmProvidersDict):
        self.log = log
        self.provider = None
        self.provider_params = None
        self.lm_providers = lm_providers

    def update(self, config: GlobalConfig):
        model_id = config.model_provider_id
        local_model_id, provider = get_lm_provider(model_id, self.lm_providers)

        if not provider:
            raise ValueError(f"No provider and model found with '{model_id}'")

        fields = config.fields.get(model_id, {})
        provider_params = {"model_id": local_model_id, **fields}

        auth_strategy = provider.auth_strategy
        if auth_strategy and auth_strategy.type == "env":
            api_keys = config.api_keys
            name = auth_strategy.name
            if name not in api_keys:
                raise ValueError(
                    f"Missing value for '{auth_strategy.name}' in the config."
                )
            provider_params[name.lower()] = api_keys[name]

        self.provider = provider
        self.provider_params = provider_params

    def get_provider(self):
        return self.provider

    def get_provider_params(self):
        return self.provider_params
