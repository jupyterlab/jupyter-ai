from ._version import __version__
from .exception import store_exception
from .extension import AiExtension
from jupyter_ai_magics import AiMagics

# imports to expose entry points. DO NOT REMOVE.
from .engine import GPT3ModelEngine
from .tasks import tasks

# imports to expose types to other AI modules. DO NOT REMOVE.
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
    ipython.set_custom_exc((BaseException,), store_exception)

def unload_ipython_extension(ipython):
    ipython.set_custom_exc((BaseException,), ipython.CustomTB)
