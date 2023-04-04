from ._version import __version__
from .extension import AiExtension
from .magics import AiMagics

# imports to expose entry points. DO NOT REMOVE.
from .engine import GPT3ModelEngine
from .tasks import tasks
from .providers import (
    AI21Provider,
    AnthropicProvider,
    CohereProvider,
    HfHubProvider,
    OpenAIProvider,
    ChatOpenAIProvider,
    SmEndpointProvider
)

# imports to expose types to other AI modules. DO NOT REMOVE.
from .providers import BaseProvider
from .tasks import DefaultTaskDefinition

def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "@jupyter-ai/core"
    }]

def _jupyter_server_extension_points():
    return [{
        "module": "jupyter_ai",
        "app": AiExtension
    }]

def load_ipython_extension(ipython):
    ipython.register_magics(AiMagics)
