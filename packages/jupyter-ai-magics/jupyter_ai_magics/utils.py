import logging
from typing import Dict, Optional, Tuple, Union
from importlib_metadata import entry_points
from jupyter_ai_magics.aliases import MODEL_ID_ALIASES

from jupyter_ai_magics.embedding_providers import BaseEmbeddingsProvider

from jupyter_ai_magics.providers import BaseProvider


Logger = Union[logging.Logger, logging.LoggerAdapter]


def load_providers(log: Optional[Logger] = None) -> Dict[str, BaseProvider]:
    if not log:
        log = logging.getLogger()
        log.addHandler(logging.NullHandler())

    providers = {}
    eps = entry_points()
    model_provider_eps = eps.select(group="jupyter_ai.model_providers")
    for model_provider_ep in model_provider_eps:
        try:
            provider = model_provider_ep.load()
        except:
            log.error(f"Unable to load model provider class from entry point `{model_provider_ep.name}`.")
            continue
        providers[provider.id] = provider
        log.info(f"Registered model provider `{provider.id}`.")
    
    return providers


def load_embedding_providers(log: Optional[Logger] = None) -> Dict[str, BaseEmbeddingsProvider]:
    if not log:
        log = logging.getLogger()
        log.addHandler(logging.NullHandler())
    providers = {}
    eps = entry_points()
    model_provider_eps = eps.select(group="jupyter_ai.embeddings_model_providers")
    for model_provider_ep in model_provider_eps:
        try:
            provider = model_provider_ep.load()
        except:
            log.error(f"Unable to load embeddings model provider class from entry point `{model_provider_ep.name}`.")
            continue
        providers[provider.id] = provider
        log.info(f"Registered embeddings model provider `{provider.id}`.")
    
    return providers

def decompose_model_id(model_id: str, providers: Dict[str, BaseProvider]) -> Tuple[str, str]:
        """Breaks down a model ID into a two-tuple (provider_id, local_model_id). Returns (None, None) if indeterminate."""
        if model_id in MODEL_ID_ALIASES:
            model_id = MODEL_ID_ALIASES[model_id]

        if ":" not in model_id:
            # case: model ID was not provided with a prefix indicating the provider
            # ID. try to infer the provider ID before returning (None, None).

            # naively search through the dictionary and return the first provider
            # that provides a model of the same ID.
            for provider_id, provider in providers.items():
                if model_id in provider.models:
                    return (provider_id, model_id)
            
            return (None, None)

        provider_id, local_model_id = model_id.split(":", 1)
        return (provider_id, local_model_id)
