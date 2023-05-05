from typing import ClassVar, Dict, List, Union, Literal, Optional

import base64

import io

from langchain.schema import BaseModel as BaseLangchainProvider
from langchain.llms import (
    AI21,
    Anthropic,
    Cohere,
    HuggingFaceHub,
    OpenAI,
    OpenAIChat,
    SagemakerEndpoint
)
from langchain.utils import get_from_dict_or_env
from langchain.llms.utils import enforce_stop_tokens

from pydantic import BaseModel, Extra, root_validator
from langchain.chat_models import ChatOpenAI

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

HUGGINGFACE_HUB_VALID_TASKS = ("text2text-generation", "text-generation", "text-to-image")

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

    # Override the parent's validate_environment with a custom list of valid tasks
    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        huggingfacehub_api_token = get_from_dict_or_env(
            values, "huggingfacehub_api_token", "HUGGINGFACEHUB_API_TOKEN"
        )
        try:
            from huggingface_hub.inference_api import InferenceApi

            repo_id = values["repo_id"]
            client = InferenceApi(
                repo_id=repo_id,
                token=huggingfacehub_api_token,
                task=values.get("task"),
            )
            if client.task not in HUGGINGFACE_HUB_VALID_TASKS:
                raise ValueError(
                    f"Got invalid task {client.task}, "
                    f"currently only {HUGGINGFACE_HUB_VALID_TASKS} are supported"
                )
            values["client"] = client
        except ImportError:
            raise ValueError(
                "Could not import huggingface_hub python package. "
                "Please install it with `pip install huggingface_hub`."
            )
        return values
    
    # Handle image outputs
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Call out to HuggingFace Hub's inference endpoint.

        Args:
            prompt: The prompt to pass into the model.
            stop: Optional list of stop words to use when generating.

        Returns:
            The string or image generated by the model.

        Example:
            .. code-block:: python

                response = hf("Tell me a joke.")
        """
        _model_kwargs = self.model_kwargs or {}
        response = self.client(inputs=prompt, params=_model_kwargs)

        if type(response) is dict and "error" in response:
            raise ValueError(f"Error raised by inference API: {response['error']}")

        # Custom code for responding to image generation responses
        if self.client.task == "text-to-image":
            imageFormat = response.format # Presume it's a PIL ImageFile
            mimeType = ''
            if (imageFormat == 'JPEG'):
                mimeType = 'image/jpeg'
            elif (imageFormat == 'PNG'):
                mimeType = 'image/png'
            elif (imageFormat == 'GIF'):
                mimeType = 'image/gif'
            else:
                raise ValueError(f"Unrecognized image format {imageFormat}")
            
            buffer = io.BytesIO()
            response.save(buffer, format=imageFormat)
            # Encode image data to Base64 bytes, then decode bytes to str
            return (mimeType + ';base64,' + base64.b64encode(buffer.getvalue()).decode())

        if self.client.task == "text-generation":
            # Text generation return includes the starter text.
            text = response[0]["generated_text"][len(prompt) :]
        elif self.client.task == "text2text-generation":
            text = response[0]["generated_text"]
        else:
            raise ValueError(
                f"Got invalid task {self.client.task}, "
                f"currently only {HUGGINGFACE_HUB_VALID_TASKS} are supported"
            )
        if stop is not None:
            # This is a bit hacky, but I can't figure out a better way to enforce
            # stop tokens when making calls to huggingface_hub.
            text = enforce_stop_tokens(text, stop)
        return text

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

    def append_exchange(self, prompt: str, output: str):
        """Appends a conversational exchange between user and an OpenAI Chat
        model to a transcript that will be included in future exchanges."""
        self.prefix_messages.append({
            "role": "user",
            "content": prompt
        })
        self.prefix_messages.append({
            "role": "assistant",
            "content": output
        })

# uses the new OpenAIChat provider. temporarily living as a separate class until
# conflicts can be resolved
class ChatOpenAINewProvider(BaseProvider, ChatOpenAI):
    id = "openai-chat-new"
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

    
