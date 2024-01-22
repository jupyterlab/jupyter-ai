from typing import ClassVar, List

from jupyter_ai_magics.providers import (
    AuthStrategy,
    AwsAuthStrategy,
    EnvAuthStrategy,
    Field,
    MultiEnvAuthStrategy,
)
from langchain.pydantic_v1 import BaseModel, Extra
from langchain_community.embeddings import (
    BedrockEmbeddings,
    CohereEmbeddings,
    GPT4AllEmbeddings,
    HuggingFaceHubEmbeddings,
    OpenAIEmbeddings,
    QianfanEmbeddingsEndpoint,
)


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

    registry: ClassVar[bool] = False
    """Whether this provider is a registry provider."""

    fields: ClassVar[List[Field]] = []
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


class OpenAIEmbeddingsProvider(BaseEmbeddingsProvider, OpenAIEmbeddings):
    id = "openai"
    name = "OpenAI"
    models = ["text-embedding-ada-002"]
    model_id_key = "model"
    pypi_package_deps = ["openai"]
    auth_strategy = EnvAuthStrategy(name="OPENAI_API_KEY")


class CohereEmbeddingsProvider(BaseEmbeddingsProvider, CohereEmbeddings):
    id = "cohere"
    name = "Cohere"
    models = [
        "embed-english-v2.0",
        "embed-english-light-v2.0",
        "embed-multilingual-v2.0",
        "embed-english-v3.0",
        "embed-english-light-v3.0",
        "embed-multilingual-v3.0",
        "embed-multilingual-light-v3.0",
    ]
    model_id_key = "model"
    pypi_package_deps = ["cohere"]
    auth_strategy = EnvAuthStrategy(name="COHERE_API_KEY")


class HfHubEmbeddingsProvider(BaseEmbeddingsProvider, HuggingFaceHubEmbeddings):
    id = "huggingface_hub"
    name = "Hugging Face Hub"
    models = ["*"]
    model_id_key = "repo_id"
    # ipywidgets needed to suppress tqdm warning
    # https://stackoverflow.com/questions/67998191
    # tqdm is a dependency of huggingface_hub
    pypi_package_deps = ["huggingface_hub", "ipywidgets"]
    auth_strategy = EnvAuthStrategy(name="HUGGINGFACEHUB_API_TOKEN")
    registry = True


class BedrockEmbeddingsProvider(BaseEmbeddingsProvider, BedrockEmbeddings):
    id = "bedrock"
    name = "Bedrock"
    models = ["amazon.titan-embed-text-v1"]
    model_id_key = "model_id"
    pypi_package_deps = ["boto3"]
    auth_strategy = AwsAuthStrategy()


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
