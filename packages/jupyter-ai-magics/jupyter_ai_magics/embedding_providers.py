from typing import ClassVar, List, Type
from jupyter_ai_magics.providers import AuthStrategy, EnvAuthStrategy
from pydantic import BaseModel, Extra
from langchain.embeddings import OpenAIEmbeddings, CohereEmbeddings, HuggingFaceHubEmbeddings
from langchain.embeddings.base import Embeddings


class BaseEmbeddingsProvider(BaseModel):
    """Base class for embedding providers"""

    class Config:
        extra = Extra.allow

    id: ClassVar[str] = ...
    """ID for this provider class."""

    name: ClassVar[str] = ...
    """User-facing name of this provider."""

    models: ClassVar[List[str]] = ...
    """List of supported models by their IDs. For registry providers, this will
    be just ["*"]."""

    model_id_key: ClassVar[str] = ...
    """Kwarg expected by the upstream LangChain provider."""

    pypi_package_deps: ClassVar[List[str]] = []
    """List of PyPi package dependencies."""

    auth_strategy: ClassVar[AuthStrategy] = None
    """Authentication/authorization strategy. Declares what credentials are
    required to use this model provider. Generally should not be `None`."""

    model_id: str

    provider_klass: ClassVar[Type[Embeddings]]    

    
class OpenAIEmbeddingsProvider(BaseEmbeddingsProvider):
    id = "openai"
    name = "OpenAI"
    models = [
        "text-embedding-ada-002"
    ]
    model_id_key = "model"
    pypi_package_deps = ["openai"]
    auth_strategy = EnvAuthStrategy(name="OPENAI_API_KEY")
    provider_klass = OpenAIEmbeddings


class CohereEmbeddingsProvider(BaseEmbeddingsProvider):
    id = "cohere"
    name = "Cohere"
    models = [
        'large',
        'multilingual-22-12',
        'small'
    ]
    model_id_key = "model"
    pypi_package_deps = ["cohere"]
    auth_strategy = EnvAuthStrategy(name="COHERE_API_KEY")
    provider_klass = CohereEmbeddings


class HfHubEmbeddingsProvider(BaseEmbeddingsProvider):
    id = "huggingface_hub"
    name = "HuggingFace Hub"
    models = ["*"]
    model_id_key = "repo_id"
    # ipywidgets needed to suppress tqdm warning
    # https://stackoverflow.com/questions/67998191
    # tqdm is a dependency of huggingface_hub
    pypi_package_deps = ["huggingface_hub", "ipywidgets"]
    auth_strategy = EnvAuthStrategy(name="HUGGINGFACEHUB_API_TOKEN")
    provider_klass = HuggingFaceHubEmbeddings
