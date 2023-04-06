from typing import ClassVar, List, Union, Literal, Optional

from langchain.schema import BaseLanguageModel as BaseLangchainProvider
from langchain.llms import (
    AI21,
    Anthropic,
    Cohere,
    HuggingFaceHub,
    OpenAI,
    OpenAIChat,
    SagemakerEndpoint
)
from pydantic import BaseModel, Extra

class EnvAuthStrategy(BaseModel):
    """Require one auth token via an environment variable."""
    type: Literal["env"] = "env"
    name: str


class MultiEnvAuthStrategy(BaseModel):
    """Require multiple auth tokens via multiple environment variables."""
    type: Literal["file"] = "file"
    names: List[str]


class AwsAuthStrategy(BaseModel):
    """Require AWS authentication via Boto3"""
    type: Literal["aws"] = "aws"


AuthStrategy = Optional[
    Union[
        EnvAuthStrategy,
        MultiEnvAuthStrategy,
        AwsAuthStrategy,
    ]
]

class BaseProvider(BaseLangchainProvider):
    #
    # pydantic config
    #
    class Config:
        extra = Extra.allow

    #
    # class attrs
    #
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

    #
    # instance attrs
    #
    model_id: str

    def __init__(self, *args, **kwargs):
        try:
            assert kwargs["model_id"]
        except:
            raise AssertionError("model_id was not specified. Please specify it as a keyword argument.")

        model_kwargs = {}
        model_kwargs[self.__class__.model_id_key] = kwargs["model_id"]

        super().__init__(*args, **kwargs, **model_kwargs)

    
class AI21Provider(BaseProvider, AI21):
    id = "ai21"
    name = "AI21"
    models = [
        "j1-large",
        "j1-grande",
        "j1-jumbo",
        "j1-grande-instruct",
        "j2-large",
        "j2-grande",
        "j2-jumbo",
        "j2-grande-instruct",
        "j2-jumbo-instruct",
    ]
    model_id_key = "model"
    pypi_package_deps = ["ai21"]
    auth_strategy = EnvAuthStrategy(name="AI21_API_KEY")

class AnthropicProvider(BaseProvider, Anthropic):
    id = "anthropic"
    name = "Anthropic"
    models = [
        "claude-v1",
        "claude-v1.0",
        "claude-v1.2",
        "claude-instant-v1",
        "claude-instant-v1.0",
    ]
    model_id_key = "model"
    pypi_package_deps = ["anthropic"]
    auth_strategy = EnvAuthStrategy(name="ANTHROPIC_API_KEY")

class CohereProvider(BaseProvider, Cohere):
    id = "cohere"
    name = "Cohere"
    models = ["medium", "xlarge"]
    model_id_key = "model"
    pypi_package_deps = ["cohere"]
    auth_strategy = EnvAuthStrategy(name="COHERE_API_KEY")

class HfHubProvider(BaseProvider, HuggingFaceHub):
    id = "huggingface_hub"
    name = "HuggingFace Hub"
    models = ["*"]
    model_id_key = "repo_id"
    # ipywidgets needed to suppress tqdm warning
    # https://stackoverflow.com/questions/67998191
    # tqdm is a dependency of huggingface_hub
    pypi_package_deps = ["huggingface_hub", "ipywidgets"]
    auth_strategy = EnvAuthStrategy(name="HUGGINGFACEHUB_API_TOKEN")

class OpenAIProvider(BaseProvider, OpenAI):
    id = "openai"
    name = "OpenAI"
    models = [
        "text-davinci-003",
        "text-davinci-002",
        "text-curie-001",
        "text-babbage-001",
        "text-ada-001",
        "davinci",
        "curie",
        "babbage",
        "ada",
    ]
    model_id_key = "model_name"
    pypi_package_deps = ["openai"]
    auth_strategy = EnvAuthStrategy(name="OPENAI_API_KEY")

class ChatOpenAIProvider(BaseProvider, OpenAIChat):
    id = "openai-chat"
    name = "OpenAI"
    models = [
        "gpt-4",
        "gpt-4-0314",
        "gpt-4-32k",
        "gpt-4-32k-0314",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0301",
    ]
    model_id_key = "model_name"
    pypi_package_deps = ["openai"]
    auth_strategy = EnvAuthStrategy(name="OPENAI_API_KEY")

class SmEndpointProvider(BaseProvider, SagemakerEndpoint):
    id = "sagemaker-endpoint"
    name = "Sagemaker Endpoint"
    models = ["*"]
    model_id_key = "endpoint_name"
    pypi_package_deps = ["boto3"]
    auth_strategy = AwsAuthStrategy()
