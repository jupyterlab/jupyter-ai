import logging
from typing import Dict, List, Literal, Optional, Tuple, Type, Union

from importlib_metadata import entry_points
from jupyter_ai_magics.aliases import MODEL_ID_ALIASES
from jupyter_ai_magics.embedding_providers import BaseEmbeddingsProvider
from jupyter_ai_magics.providers import BaseProvider

Logger = Union[logging.Logger, logging.LoggerAdapter]
LmProvidersDict = Dict[str, BaseProvider]
EmProvidersDict = Dict[str, BaseEmbeddingsProvider]
AnyProvider = Union[BaseProvider, BaseEmbeddingsProvider]
ProviderDict = Dict[str, AnyProvider]
ProviderRestrictions = Dict[
    Literal["allowed_providers", "blocked_providers"], Optional[List[str]]
]


def get_lm_providers(
    log: Optional[Logger] = None, restrictions: Optional[ProviderRestrictions] = None
) -> LmProvidersDict:
    if not log:
        log = logging.getLogger()
        log.addHandler(logging.NullHandler())
    if not restrictions:
        restrictions = {"allowed_providers": None, "blocked_providers": None}
    providers = {}
    eps = entry_points()
    provider_ep_group = eps.select(group="jupyter_ai.model_providers")
    for provider_ep in provider_ep_group:
        try:
            provider = provider_ep.load()
        except ImportError as e:
            log.warning(
                f"Unable to load model provider `{provider_ep.name}`. Please install the `{e.name}` package."
            )
            continue
        except Exception as e:
            log.error(
                f"Unable to load model provider `{provider_ep.name}`. Printing full exception below."
            )
            log.exception(e)
            continue

        if not is_provider_allowed(provider.id, restrictions):
            log.info(f"Skipping blocked provider `{provider.id}`.")
            continue
        providers[provider.id] = provider
        log.info(f"Registered model provider `{provider.id}`.")

    return providers


def get_em_providers(
    log: Optional[Logger] = None, restrictions: Optional[ProviderRestrictions] = None
) -> EmProvidersDict:
    if not log:
        log = logging.getLogger()
        log.addHandler(logging.NullHandler())
    if not restrictions:
        restrictions = {"allowed_providers": None, "blocked_providers": None}
    providers = {}
    eps = entry_points()
    model_provider_eps = eps.select(group="jupyter_ai.embeddings_model_providers")
    for model_provider_ep in model_provider_eps:
        try:
            provider = model_provider_ep.load()
        except Exception as e:
            log.error(
                f"Unable to load embeddings model provider class from entry point `{model_provider_ep.name}`: %s.",
                e,
            )
            continue
        if not is_provider_allowed(provider.id, restrictions):
            log.info(f"Skipping blocked provider `{provider.id}`.")
            continue
        providers[provider.id] = provider
        log.info(f"Registered embeddings model provider `{provider.id}`.")

    return providers


def decompose_model_id(
    model_id: str, providers: Dict[str, BaseProvider]
) -> Tuple[str, str]:
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


def get_lm_provider(
    model_id: str, lm_providers: LmProvidersDict
) -> Tuple[str, Type[BaseProvider]]:
    """Gets a two-tuple (<local-model-id>, <provider-class>) specified by a
    global model ID."""
    return _get_provider(model_id, lm_providers)


def get_em_provider(
    model_id: str, em_providers: EmProvidersDict
) -> Tuple[str, Type[BaseEmbeddingsProvider]]:
    """Gets a two-tuple (<local-model-id>, <provider-class>) specified by a
    global model ID."""
    return _get_provider(model_id, em_providers)


def is_provider_allowed(provider_id: str, restrictions: ProviderRestrictions) -> bool:
    allowed = restrictions["allowed_providers"]
    blocked = restrictions["blocked_providers"]
    if blocked and provider_id in blocked:
        return False
    if allowed and provider_id not in allowed:
        return False
    return True


def _get_provider(model_id: str, providers: ProviderDict):
    provider_id, local_model_id = decompose_model_id(model_id, providers)
    provider = providers.get(provider_id, None)
    return local_model_id, provider
