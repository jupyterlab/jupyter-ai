from jupyter_ai.actors.base import Logger, ACTOR_TYPE
from jupyter_ai.models import GlobalConfig
import ray

@ray.remote
class EmbeddingsProviderActor():

    def __init__(self, log: Logger):
        self.log = log
        self.provider = None
        self.provider_params = None
        self.model_id = None

    def update(self, config: GlobalConfig):
        model_id = config.embeddings_provider_id
        actor = ray.get_actor(ACTOR_TYPE.PROVIDERS.value)
        local_model_id, provider = ray.get(
            actor.get_embeddings_provider_data.remote(model_id)
        )
        
        if not provider:
            raise ValueError(f"No provider and model found with '{model_id}'")
        
        provider_params = {}
        provider_params[provider.model_id_key] = local_model_id
        
        auth_strategy = provider.auth_strategy
        if auth_strategy and auth_strategy.type == "env":
            api_keys = config.api_keys
            name = auth_strategy.name
            if name not in api_keys:
                raise ValueError(f"Missing value for '{auth_strategy.name}' in the config.")
            provider_params[name.lower()] = api_keys[name]
            
        self.provider = provider.provider_klass
        self.provider_params = provider_params
        previous_model_id = self.model_id
        self.model_id = model_id
        
        if previous_model_id and previous_model_id != model_id:
            # delete the index
            actor = ray.get_actor(ACTOR_TYPE.LEARN)
            actor.delete_and_relearn.remote()

    def get_provider(self):
        return self.provider
    
    def get_provider_params(self):
        return self.provider_params
    
    def get_model_id(self):
        return self.model_id