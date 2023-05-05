from jupyter_ai.actors.base import Logger, ACTOR_TYPE
from jupyter_ai.models import GlobalConfig
import ray

@ray.remote
class ChatProviderActor():

    def __init__(self, log: Logger):
        self.log = log
        self.provider = None
        self.provider_params = None

    def update(self, config: GlobalConfig):
        model_id = config.model_provider_id
        actor = ray.get_actor(ACTOR_TYPE.PROVIDERS.value)
        local_model_id, provider = ray.get(
            actor.get_model_provider_data.remote(model_id)
        )
        
        if not provider:
            raise ValueError(f"No provider and model found with '{model_id}'")
        
        provider_params = { "model_id": local_model_id}
        
        auth_strategy = provider.auth_strategy
        if auth_strategy and auth_strategy.type == "env":
            api_keys = config.api_keys
            name = auth_strategy.name
            if name not in api_keys:
                raise ValueError(f"Missing value for '{auth_strategy.name}' in the config.")
            provider_params[name.lower()] = api_keys[name]
            
        self.provider = provider
        self.provider_params = provider_params

    def get_provider(self):
        return self.provider
    
    def get_provider_params(self):
        return self.provider_params