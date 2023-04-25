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
    
    def get_embeddings_providers(self):
        return self.embeddings_providers

    