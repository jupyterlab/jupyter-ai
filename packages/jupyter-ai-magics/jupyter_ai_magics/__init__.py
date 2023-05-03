from ._version import __version__
from .exception import store_exception
from .magics import AiMagics

# expose model providers on the package root
from .providers import (
    AI21Provider,
    AnthropicProvider,
    CohereProvider,
    HfHubProvider,
    OpenAIProvider,
    ChatOpenAIProvider,
    ChatOpenAINewProvider,
    SmEndpointProvider
)
# expose embedding model providers on the package root
from .embedding_providers import (
    OpenAIEmbeddingsProvider,
    CohereEmbeddingsProvider,
    HfHubEmbeddingsProvider
)
from .providers import BaseProvider

def load_ipython_extension(ipython):
    ipython.register_magics(AiMagics)
    ipython.set_custom_exc((BaseException,), store_exception)

def unload_ipython_extension(ipython):
    ipython.set_custom_exc((BaseException,), ipython.CustomTB)
