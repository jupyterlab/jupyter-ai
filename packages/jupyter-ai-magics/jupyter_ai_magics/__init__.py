from ._version import __version__

from .magics import AiMagics

# expose model providers on the package root
from .providers import (
    AI21Provider,
    AnthropicProvider,
    CohereProvider,
    HfHubProvider,
    OpenAIProvider,
    ChatOpenAIProvider,
    SmEndpointProvider
)
from .providers import BaseProvider

def load_ipython_extension(ipython):
    ipython.register_magics(AiMagics)