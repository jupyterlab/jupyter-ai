from typing import Optional
from jupyter_ai_magics.utils import load_embedding_providers, load_providers
import ray
from jupyter_ai.actors.base import BaseActor, Logger
from ray.util.queue import Queue

@ray.remote
class ProvidersActor():
    
    def __init__(self, log: Logger):
        self.log = log
        self.model_providers = load_providers(log=log)
        self.embeddings_providers = load_embedding_providers(log=log)

    def get_model_providers(self):
        return self.model_providers
    
    def get_model_provider(self, provider_id: Optional[str]):
        if provider_id is None or provider_id not in self.model_providers:
            return None

        return self.model_providers[provider_id]
    
    def get_embeddings_provider(self, provider_id: Optional[str]):
        if provider_id is None or provider_id not in self.embeddings_providers:
            return None

        return self.embeddings_providers[provider_id]
    
    def get_embeddings_providers(self):
        return self.embeddings_providers

    