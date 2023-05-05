from typing import Optional, Tuple, Type
from jupyter_ai_magics.embedding_providers import BaseEmbeddingsProvider
from jupyter_ai_magics.providers import BaseProvider
from jupyter_ai_magics.utils import decompose_model_id, load_embedding_providers, load_providers
import ray
from jupyter_ai.actors.base import BaseActor, Logger
from ray.util.queue import Queue

@ray.remote
class ProvidersActor():
    """Actor that loads model and embedding providers from,
    entry points. Also provides utility functions to get the 
    providers and provider class matching a provider id.
    """
    
    def __init__(self, log: Logger):
        self.log = log
        self.model_providers = load_providers(log=log)
        self.embeddings_providers = load_embedding_providers(log=log)

    def get_model_providers(self):
        """Returns dictionary of registered LLM providers"""
        return self.model_providers
    
    def get_model_provider_data(self, model_id: str) -> Tuple[str, Type[BaseProvider]]:
        """Returns the model provider class that matches the provider id"""
        provider_id, local_model_id = decompose_model_id(model_id, self.model_providers)
        provider = self.model_providers.get(provider_id, None)
        return local_model_id, provider
    
    def get_embeddings_providers(self):
        """Returns dictionary of registered embedding providers"""
        return self.embeddings_providers

    def get_embeddings_provider_data(self, model_id: str) -> Tuple[str, Type[BaseEmbeddingsProvider]]:
        """Returns the embedding provider class that matches the provider id"""
        provider_id, local_model_id = decompose_model_id(model_id, self.embeddings_providers)
        provider = self.embeddings_providers.get(provider_id, None)
        return local_model_id, provider
    

    