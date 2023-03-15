from ._version import __version__

# expose engines and tasks on the module root so that they may be declared as
# entrypoints in `pyproject.toml`
from .engine import ChatGptModelEngine

def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "@jupyter-ai/chatgpt"
    }]
