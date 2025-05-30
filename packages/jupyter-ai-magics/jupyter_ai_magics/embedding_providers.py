from typing import ClassVar, Optional

from jupyter_ai_magics.base_provider import (
    AuthStrategy,
    EnvAuthStrategy,
    Field,
    MultiEnvAuthStrategy,
)
from langchain_community.embeddings import (
    GPT4AllEmbeddings,
    HuggingFaceHubEmbeddings,
    QianfanEmbeddingsEndpoint,
)
from pydantic import BaseModel, ConfigDict


class BaseEmbeddingsProvider(BaseModel):
    """Base class for embedding providers"""

    # pydantic v2 model config
    # upstream docs: https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra
    model_config = ConfigDict(extra="allow")

    id: ClassVar[str] = ...
    """ID for this provider class."""

    name: ClassVar[str] = ...
    """User-facing name of this provider."""

    models: ClassVar[list[str]] = ...
    """List of supported models by their IDs. For registry providers, this will
    be just ["*"]."""

    help: ClassVar[Optional[str]] = None
    """Text to display in lieu of a model list for a registry provider that does
    not provide a list of models."""

    model_id_key: ClassVar[str] = ...
    """Kwarg expected by the upstream LangChain provider."""

    pypi_package_deps: ClassVar[list[str]] = []
    """List of PyPi package dependencies."""

    auth_strategy: ClassVar[AuthStrategy] = None
    """Authentication/authorization strategy. Declares what credentials are
    required to use this model provider. Generally should not be `None`."""

    model_id: str

    registry: ClassVar[bool] = False
    """Whether this provider is a registry provider."""

    fields: ClassVar[list[Field]] = []
    """Fields expected by this provider in its constructor. Each `Field` `f`
    should be passed as a keyword argument, keyed by `f.key`."""

    def __init__(self, *args, **kwargs):
        try:
            assert kwargs["model_id"]
        except:
            raise AssertionError(
                "model_id was not specified. Please specify it as a keyword argument."
            )

        model_kwargs = {}
        if self.__class__.model_id_key != "model_id":
            model_kwargs[self.__class__.model_id_key] = kwargs["model_id"]

        super().__init__(*args, **kwargs, **model_kwargs)


class HfHubEmbeddingsProvider(BaseEmbeddingsProvider, HuggingFaceHubEmbeddings):
    id = "huggingface_hub"
    name = "Hugging Face Hub"
    models = ["*"]
    model_id_key = "repo_id"
    help = (
        "See [https://huggingface.co/docs/chat-ui/en/configuration/embeddings](https://huggingface.co/docs/chat-ui/en/configuration/embeddings) for reference. "
        "Pass an embedding model's name; for example, `sentence-transformers/all-MiniLM-L6-v2`."
    )
    # ipywidgets needed to suppress tqdm warning
    # https://stackoverflow.com/questions/67998191
    # tqdm is a dependency of huggingface_hub
    pypi_package_deps = ["huggingface_hub", "ipywidgets"]
    auth_strategy = EnvAuthStrategy(name="HUGGINGFACEHUB_API_TOKEN")
    registry = True


class GPT4AllEmbeddingsProvider(BaseEmbeddingsProvider, GPT4AllEmbeddings):
    def __init__(self, **kwargs):
        from gpt4all import GPT4All

        model_name = kwargs.get("model_id").split(":")[-1]

        # GPT4AllEmbeddings doesn't allow any kwargs at the moment
        # This will cause the class to start downloading the model
        # if the model file is not present. Calling retrieve_model
        # here will throw an exception if the file is not present.
        GPT4All.retrieve_model(model_name=model_name, allow_download=False)

        kwargs["allow_download"] = False
        super().__init__(**kwargs)

    id = "gpt4all"
    name = "GPT4All Embeddings"
    models = ["all-MiniLM-L6-v2-f16"]
    model_id_key = "model_id"
    pypi_package_deps = ["gpt4all"]


class QianfanEmbeddingsEndpointProvider(
    BaseEmbeddingsProvider, QianfanEmbeddingsEndpoint
):
    id = "qianfan"
    name = "ERNIE-Bot"
    models = ["ERNIE-Bot", "ERNIE-Bot-4"]
    model_id_key = "model"
    pypi_package_deps = ["qianfan"]
    auth_strategy = MultiEnvAuthStrategy(names=["QIANFAN_AK", "QIANFAN_SK"])
