from ._version import __version__

# expose ChatGptModelEngine on the root module so that it may be declared as an
# entrypoint in `pyproject.toml`
from .engine import ChatGptModelEngine


def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "@jupyter-ai/chatgpt"
    }]
