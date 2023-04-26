


from typing import Optional
from jupyter_ai.actors.base import Logger, ACTOR_TYPE
from jupyter_ai.models import ProviderConfig
from jupyter_ai_magics.utils import decompose_model_id
import ray

@ray.remote
class EmbeddingsProviderActor():

    def __init__(self, log: Logger):
        self.log = log
        self.provider = None
        self.provider_params = None

    def update(self, config: ProviderConfig):
        providers_actor = ray.get_actor(ACTOR_TYPE.PROVIDERS.value)
        o = providers_actor.get_embeddings_providers.remote()
        providers = ray.get(o)
        provider_id, local_model_id = decompose_model_id(model_id=config.embeddings_provider, providers=providers)

        p = providers_actor.get_embeddings_provider.remote(provider_id)
        provider = ray.get(p)
        if not provider:
            return
        
        auth_strategy = provider.auth_strategy
        api_keys = config.api_keys
        if auth_strategy:
            if auth_strategy.type == "env" and auth_strategy.name.lower() not in api_keys:
                # raise error?
                return
            
            provider_params = {}
            provider_params[provider.model_id_key] = local_model_id
            api_key_name = auth_strategy.name.lower()
            provider_params[api_key_name] = api_keys[api_key_name]
            self.provider = provider.provider_klass
            self.provider_params = provider_params

    def get_provider(self):
        return self.provider
    
    def get_provider_params(self):
        return self.provider_params