from typing import TYPE_CHECKING

from ._import_utils import import_attr as _import_attr
from ._version import __version__

if TYPE_CHECKING:
    # same as dynamic imports but understood by mypy
    from .embedding_providers import (
        BaseEmbeddingsProvider,
        GPT4AllEmbeddingsProvider,
        HfHubEmbeddingsProvider,
        QianfanEmbeddingsEndpointProvider,
    )
    from .exception import store_exception
    from .magics import AiMagics
    from .models.persona import JupyternautPersona, Persona
    from .providers import (
        AI21Provider,
        BaseProvider,
        GPT4AllProvider,
        HfHubProvider,
        QianfanProvider,
        TogetherAIProvider,
    )
else:
    _exports_by_module = {
        # expose embedding model providers on the package root
        "embedding_providers": [
            "BaseEmbeddingsProvider",
            "GPT4AllEmbeddingsProvider",
            "HfHubEmbeddingsProvider",
            "QianfanEmbeddingsEndpointProvider",
        ],
        "exception": ["store_exception"],
        "magics": ["AiMagics"],
        # expose JupyternautPersona on the package root
        # required by `jupyter-ai`.
        "models.persona": ["JupyternautPersona", "Persona"],
        # expose model providers on the package root
        "providers": [
            "AI21Provider",
            "BaseProvider",
            "GPT4AllProvider",
            "HfHubProvider",
            "QianfanProvider",
            "TogetherAIProvider",
        ],
    }

    _modules_by_export = {
        import_name: module
        for module, imports in _exports_by_module.items()
        for import_name in imports
    }

    def __getattr__(export_name: str) -> object:
        module_name = _modules_by_export.get(export_name)
        result = _import_attr(export_name, module_name, __spec__.parent)
        globals()[export_name] = result
        return result


def load_ipython_extension(ipython):
    ipython.register_magics(__getattr__("AiMagics"))
    ipython.set_custom_exc((BaseException,), __getattr__("store_exception"))


def unload_ipython_extension(ipython):
    ipython.set_custom_exc((BaseException,), ipython.CustomTB)


# required to preserve backward compatibility with `from jupyter_ai_magics import *`
__all__ = [
    "__version__",
    "load_ipython_extension",
    "unload_ipython_extension",
    "BaseEmbeddingsProvider",
    "GPT4AllEmbeddingsProvider",
    "HfHubEmbeddingsProvider",
    "QianfanEmbeddingsEndpointProvider",
    "store_exception",
    "AiMagics",
    "JupyternautPersona",
    "Persona",
    "AI21Provider",
    "BaseProvider",
    "GPT4AllProvider",
    "HfHubProvider",
    "QianfanProvider",
    "TogetherAIProvider",
]


def __dir__():
    # Allows more editors (e.g. IPython) to complete on `jupyter_ai_magics.<tab>`
    return list(__all__)
