from ._version import __version__
from .extension import AiExtension
from .engine import GPT3ModelEngine

def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "jupyter_ai"
    }]

def _jupyter_server_extension_points():
    return [{
        "module": "jupyter_ai",
        "app": AiExtension
    }]
