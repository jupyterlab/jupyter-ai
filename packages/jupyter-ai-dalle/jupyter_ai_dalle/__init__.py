from ._version import __version__

# expose engines and tasks on the module root so that they may be declared as
# entrypoints in `pyproject.toml`
from .engine import DalleModelEngine
from .tasks import tasks

def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "@jupyter-ai/dalle"
    }]
