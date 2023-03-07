from ._version import __version__

# expose DalleModelEngine on the root module so that it may be declared as an
# entrypoint in `pyproject.toml`
from .engine import DalleModelEngine


def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "jupyter_ai_dalle"
    }]
