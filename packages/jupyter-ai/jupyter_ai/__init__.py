# The following import is to make sure jupyter_ydoc is imported before
# jupyterlab_chat, otherwise it leads to circular import because of the
# YChat relying on YBaseDoc, and jupyter_ydoc registering YChat from the entry point.
import jupyter_ydoc

# expose jupyter_ai_magics ipython extension
# DO NOT REMOVE.
from jupyter_ai_magics import load_ipython_extension, unload_ipython_extension

# expose jupyter_ai_magics providers
# DO NOT REMOVE.
from jupyter_ai_magics.providers import *

from ._version import __version__
from .extension import AiExtension


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "@jupyter-ai/core"}]


def _jupyter_server_extension_points():
    return [{"module": "jupyter_ai", "app": AiExtension}]
