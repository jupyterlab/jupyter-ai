# expose jupyter_ai_magics ipython extension
from jupyter_ai_magics import load_ipython_extension, unload_ipython_extension

from ._version import __version__

# imports to expose entry points. DO NOT REMOVE.
from .extension import AiExtension


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "@jupyter-ai/core"}]


def _jupyter_server_extension_points():
    return [{"module": "jupyter_ai", "app": AiExtension}]
