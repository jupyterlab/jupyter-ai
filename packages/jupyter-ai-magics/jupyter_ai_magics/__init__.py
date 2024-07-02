from ._version import __version__

# expose embedding model providers on the package root
from .embedding_providers import (
    BaseEmbeddingsProvider,
    BedrockEmbeddingsProvider,
    CohereEmbeddingsProvider,
    GPT4AllEmbeddingsProvider,
    HfHubEmbeddingsProvider,
    OllamaEmbeddingsProvider,
    QianfanEmbeddingsEndpointProvider,
)
from .exception import store_exception
from .magics import AiMagics

# expose JupyternautPersona on the package root
# required by `jupyter-ai`.
from .models.persona import JupyternautPersona, Persona

# expose model providers on the package root
from .providers import (
    AI21Provider,
    BaseProvider,
    BedrockChatProvider,
    BedrockProvider,
    CohereProvider,
    GPT4AllProvider,
    HfHubProvider,
    OllamaProvider,
    QianfanProvider,
    SmEndpointProvider,
    TogetherAIProvider,
)


def load_ipython_extension(ipython):
    ipython.register_magics(AiMagics)
    ipython.set_custom_exc((BaseException,), store_exception)


def unload_ipython_extension(ipython):
    ipython.set_custom_exc((BaseException,), ipython.CustomTB)
