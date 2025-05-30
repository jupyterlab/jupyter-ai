from ._import_utils import import_attr
from ._version import __version__

_dynamic_imports = {
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

_dynamic_imports_map = {
    import_name: module
    for module, imports in _dynamic_imports.items()
    for import_name in imports
}


def __getattr__(attr_name: str) -> object:
    module_name = _dynamic_imports_map.get(attr_name)
    result = import_attr(attr_name, module_name, __spec__.parent)
    globals()[attr_name] = result
    return result


def load_ipython_extension(ipython):
    ipython.register_magics(__getattr__("AiMagics"))
    ipython.set_custom_exc((BaseException,), __getattr__("store_exception"))


def unload_ipython_extension(ipython):
    ipython.set_custom_exc((BaseException,), ipython.CustomTB)


# required to preserve backward compatibiliy with `from jupyter_ai_magics import *`
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
assert set(_dynamic_imports_map.keys()) - set(__all__) == set()
