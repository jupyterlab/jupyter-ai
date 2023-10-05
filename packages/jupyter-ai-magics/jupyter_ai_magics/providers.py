import asyncio
import base64
import copy
import functools
import io
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any, ClassVar, Coroutine, Dict, List, Literal, Optional, Union

from jsonpath_ng import parse
from langchain.chat_models import (
    AzureChatOpenAI,
    BedrockChat,
    ChatAnthropic,
    ChatOpenAI,
)
from langchain.chat_models.base import BaseChatModel
from langchain.llms import (
    AI21,
    Anthropic,
    Bedrock,
    Cohere,
    GPT4All,
    HuggingFaceHub,
    OpenAI,
    OpenAIChat,
    SagemakerEndpoint,
)
from langchain.llms.sagemaker_endpoint import LLMContentHandler
from langchain.llms.utils import enforce_stop_tokens
from langchain.prompts import PromptTemplate
from langchain.schema import LLMResult
from langchain.utils import get_from_dict_or_env
from pydantic import BaseModel, Extra, root_validator


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


class Field(BaseModel):
    key: str
    label: str
    # "text" accepts any text
    format: Literal["json", "jsonpath", "text"]


class TextField(Field):
    type: Literal["text"] = "text"


class MultilineTextField(Field):
    type: Literal["text-multiline"] = "text-multiline"


class IntegerField(BaseModel):
    type: Literal["integer"] = "integer"
    key: str
    label: str


Field = Union[TextField, MultilineTextField, IntegerField]


class BaseProvider(BaseModel):
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

    help: ClassVar[str] = None
    """Text to display in lieu of a model list for a registry provider that does
    not provide a list of models."""

    model_id_key: ClassVar[str] = ...
    """Kwarg expected by the upstream LangChain provider."""

    model_id_label: ClassVar[str] = ""
    """Human-readable label of the model ID."""

    pypi_package_deps: ClassVar[List[str]] = []
    """List of PyPi package dependencies."""

    auth_strategy: ClassVar[AuthStrategy] = None
    """Authentication/authorization strategy. Declares what credentials are
    required to use this model provider. Generally should not be `None`."""

    registry: ClassVar[bool] = False
    """Whether this provider is a registry provider."""

    fields: ClassVar[List[Field]] = []
    """User inputs expected by this provider when initializing it. Each `Field` `f`
    should be passed in the constructor as a keyword argument, keyed by `f.key`."""

    #
    # instance attrs
    #
    model_id: str
    prompt_templates: Dict[str, PromptTemplate]
    """Prompt templates for each output type. Can be overridden with
    `update_prompt_template`. The function `prompt_template`, in the base class,
    refers to this."""

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

        model_kwargs["prompt_templates"] = {
            "code": PromptTemplate.from_template(
                "{prompt}\n\nProduce output as source code only, "
                "with no text or explanation before or after it."
            ),
            "html": PromptTemplate.from_template(
                "{prompt}\n\nProduce output in HTML format only, "
                "with no markup before or afterward."
            ),
            "image": PromptTemplate.from_template(
                "{prompt}\n\nProduce output as an image only, "
                "with no text before or after it."
            ),
            "markdown": PromptTemplate.from_template(
                "{prompt}\n\nProduce output in markdown format only."
            ),
            "md": PromptTemplate.from_template(
                "{prompt}\n\nProduce output in markdown format only."
            ),
            "math": PromptTemplate.from_template(
                "{prompt}\n\nProduce output in LaTeX format only, "
                "with $$ at the beginning and end."
            ),
            "json": PromptTemplate.from_template(
                "{prompt}\n\nProduce output in JSON format only, "
                "with nothing before or after it."
            ),
            "text": PromptTemplate.from_template("{prompt}"),  # No customization
        }

        super().__init__(*args, **kwargs, **model_kwargs)

    async def _call_in_executor(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        """
        Calls self._call() asynchronously in a separate thread for providers
        without an async implementation. Requires the event loop to be running.
        """
        executor = ThreadPoolExecutor(max_workers=1)
        loop = asyncio.get_running_loop()
        _call_with_args = functools.partial(self._call, *args, **kwargs)
        return await loop.run_in_executor(executor, _call_with_args)

    async def _generate_in_executor(
        self, *args, **kwargs
    ) -> Coroutine[Any, Any, LLMResult]:
        """
        Calls self._generate() asynchronously in a separate thread for providers
        without an async implementation. Requires the event loop to be running.
        """
        executor = ThreadPoolExecutor(max_workers=1)
        loop = asyncio.get_running_loop()
        _call_with_args = functools.partial(self._generate, *args, **kwargs)
        return await loop.run_in_executor(executor, _call_with_args)

    def update_prompt_template(self, format: str, template: str):
        """
        Changes the class-level prompt template for a given format.
        """
        self.prompt_templates[format] = PromptTemplate.from_template(template)

    def get_prompt_template(self, format) -> PromptTemplate:
        """
        Produce a prompt template suitable for use with a particular model, to
        produce output in a desired format.
        """

        if format in self.prompt_templates:
            return self.prompt_templates[format]
        else:
            return self.prompt_templates["text"]  # Default to plain format

    @property
    def is_chat_provider(self):
        return isinstance(self, BaseChatModel)


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

    async def _acall(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        return await self._call_in_executor(*args, **kwargs)


class AnthropicProvider(BaseProvider, Anthropic):
    id = "anthropic"
    name = "Anthropic"
    models = [
        "claude-v1",
        "claude-v1.0",
        "claude-v1.2",
        "claude-2",
        "claude-2.0",
        "claude-instant-v1",
        "claude-instant-v1.0",
        "claude-instant-v1.2",
    ]
    model_id_key = "model"
    pypi_package_deps = ["anthropic"]
    auth_strategy = EnvAuthStrategy(name="ANTHROPIC_API_KEY")


class ChatAnthropicProvider(BaseProvider, ChatAnthropic):
    id = "anthropic-chat"
    name = "ChatAnthropic"
    models = [
        "claude-v1",
        "claude-v1.0",
        "claude-v1.2",
        "claude-2",
        "claude-2.0",
        "claude-instant-v1",
        "claude-instant-v1.0",
        "claude-instant-v1.2",
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

    async def _acall(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        return await self._call_in_executor(*args, **kwargs)


class GPT4AllProvider(BaseProvider, GPT4All):
    def __init__(self, **kwargs):
        model = kwargs.get("model_id")
        if model == "ggml-gpt4all-l13b-snoozy":
            kwargs["backend"] = "llama"
        else:
            kwargs["backend"] = "gptj"

        kwargs["allow_download"] = False
        n_threads = kwargs.get("n_threads", None)
        if n_threads is not None:
            kwargs["n_threads"] = max(int(n_threads), 1)
        super().__init__(**kwargs)

    id = "gpt4all"
    name = "GPT4All"
    docs = "https://docs.gpt4all.io/gpt4all_python.html"
    models = [
        "ggml-gpt4all-j-v1.2-jazzy",
        "ggml-gpt4all-j-v1.3-groovy",
        # this one needs llama backend and has licence restriction
        "ggml-gpt4all-l13b-snoozy",
    ]
    model_id_key = "model"
    pypi_package_deps = ["gpt4all"]
    auth_strategy = None
    fields = [IntegerField(key="n_threads", label="CPU thread count (optional)")]

    async def _acall(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        return await self._call_in_executor(*args, **kwargs)


HUGGINGFACE_HUB_VALID_TASKS = (
    "text2text-generation",
    "text-generation",
    "text-to-image",
)


class HfHubProvider(BaseProvider, HuggingFaceHub):
    id = "huggingface_hub"
    name = "Hugging Face Hub"
    models = ["*"]
    model_id_key = "repo_id"
    help = (
        "See [https://huggingface.co/models](https://huggingface.co/models) for a list of models. "
        "Pass a model's repository ID as the model ID; for example, `huggingface_hub:ExampleOwner/example-model`."
    )
    # ipywidgets needed to suppress tqdm warning
    # https://stackoverflow.com/questions/67998191
    # tqdm is a dependency of huggingface_hub
    pypi_package_deps = ["huggingface_hub", "ipywidgets"]
    auth_strategy = EnvAuthStrategy(name="HUGGINGFACEHUB_API_TOKEN")
    registry = True

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
        """Call out to Hugging Face Hub's inference endpoint.

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
            imageFormat = response.format  # Presume it's a PIL ImageFile
            mimeType = ""
            if imageFormat == "JPEG":
                mimeType = "image/jpeg"
            elif imageFormat == "PNG":
                mimeType = "image/png"
            elif imageFormat == "GIF":
                mimeType = "image/gif"
            else:
                raise ValueError(f"Unrecognized image format {imageFormat}")

            buffer = io.BytesIO()
            response.save(buffer, format=imageFormat)
            # Encode image data to Base64 bytes, then decode bytes to str
            return mimeType + ";base64," + base64.b64encode(buffer.getvalue()).decode()

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

    async def _acall(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        return await self._call_in_executor(*args, **kwargs)


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
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-0301",
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4",
        "gpt-4-0314",
        "gpt-4-0613",
        "gpt-4-32k",
        "gpt-4-32k-0314",
        "gpt-4-32k-0613",
    ]
    model_id_key = "model_name"
    pypi_package_deps = ["openai"]
    auth_strategy = EnvAuthStrategy(name="OPENAI_API_KEY")

    def append_exchange(self, prompt: str, output: str):
        """Appends a conversational exchange between user and an OpenAI Chat
        model to a transcript that will be included in future exchanges."""
        self.prefix_messages.append({"role": "user", "content": prompt})
        self.prefix_messages.append({"role": "assistant", "content": output})


# uses the new OpenAIChat provider. temporarily living as a separate class until
# conflicts can be resolved
class ChatOpenAINewProvider(BaseProvider, ChatOpenAI):
    id = "openai-chat-new"
    name = "OpenAI"
    models = [
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-0301",
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4",
        "gpt-4-0314",
        "gpt-4-0613",
        "gpt-4-32k",
        "gpt-4-32k-0314",
        "gpt-4-32k-0613",
    ]
    model_id_key = "model_name"
    pypi_package_deps = ["openai"]
    auth_strategy = EnvAuthStrategy(name="OPENAI_API_KEY")

    fields = [
        TextField(
            key="openai_api_base", label="Base API URL (optional)", format="text"
        ),
        TextField(
            key="openai_organization", label="Organization (optional)", format="text"
        ),
        TextField(key="openai_proxy", label="Proxy (optional)", format="text"),
    ]


class AzureChatOpenAIProvider(BaseProvider, AzureChatOpenAI):
    id = "azure-chat-openai"
    name = "Azure OpenAI"
    models = ["*"]
    model_id_key = "deployment_name"
    model_id_label = "Deployment name"
    pypi_package_deps = ["openai"]
    auth_strategy = EnvAuthStrategy(name="OPENAI_API_KEY")
    registry = True

    fields = [
        TextField(
            key="openai_api_base", label="Base API URL (required)", format="text"
        ),
        TextField(
            key="openai_api_version", label="API version (required)", format="text"
        ),
        TextField(
            key="openai_organization", label="Organization (optional)", format="text"
        ),
        TextField(key="openai_proxy", label="Proxy (optional)", format="text"),
    ]


class JsonContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def __init__(self, request_schema, response_path):
        self.request_schema = json.loads(request_schema)
        self.response_path = response_path
        self.response_parser = parse(response_path)

    def replace_values(self, old_val, new_val, d: Dict[str, Any]):
        """Replaces values of a dictionary recursively."""
        for key, val in d.items():
            if val == old_val:
                d[key] = new_val
            if isinstance(val, dict):
                self.replace_values(old_val, new_val, val)

        return d

    def transform_input(self, prompt: str, model_kwargs: Dict) -> bytes:
        request_obj = copy.deepcopy(self.request_schema)
        self.replace_values("<prompt>", prompt, request_obj)
        request = json.dumps(request_obj).encode("utf-8")
        return request

    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        matches = self.response_parser.find(response_json)
        return matches[0].value


class SmEndpointProvider(BaseProvider, SagemakerEndpoint):
    id = "sagemaker-endpoint"
    name = "SageMaker endpoint"
    models = ["*"]
    model_id_key = "endpoint_name"
    model_id_label = "Endpoint name"
    # This all needs to be on one line of markdown, for use in a table
    help = (
        "Specify an endpoint name as the model ID. "
        "In addition, you must specify a region name, request schema, and response path. "
        "For more information, see the documentation about [SageMaker endpoints deployment](https://docs.aws.amazon.com/sagemaker/latest/dg/realtime-endpoints-deployment.html) "
        "and about [using magic commands with SageMaker endpoints](https://jupyter-ai.readthedocs.io/en/latest/users/index.html#using-magic-commands-with-sagemaker-endpoints)."
    )

    pypi_package_deps = ["boto3"]
    auth_strategy = AwsAuthStrategy()
    registry = True
    fields = [
        TextField(key="region_name", label="Region name (required)", format="text"),
        MultilineTextField(
            key="request_schema", label="Request schema (required)", format="json"
        ),
        TextField(
            key="response_path", label="Response path (required)", format="jsonpath"
        ),
    ]

    def __init__(self, *args, **kwargs):
        request_schema = kwargs.pop("request_schema")
        response_path = kwargs.pop("response_path")
        content_handler = JsonContentHandler(
            request_schema=request_schema, response_path=response_path
        )
        super().__init__(*args, **kwargs, content_handler=content_handler)

    async def _acall(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        return await self._call_in_executor(*args, **kwargs)


class BedrockProvider(BaseProvider, Bedrock):
    id = "bedrock"
    name = "Amazon Bedrock"
    models = [
        "amazon.titan-text-express-v1",
        "ai21.j2-ultra-v1",
        "ai21.j2-mid-v1",
        "cohere.command-text-v14",
    ]
    model_id_key = "model_id"
    pypi_package_deps = ["boto3"]
    auth_strategy = AwsAuthStrategy()
    fields = [
        TextField(
            key="credentials_profile_name",
            label="AWS profile (optional)",
            format="text",
        ),
        TextField(key="region_name", label="Region name (optional)", format="text"),
    ]

    async def _acall(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        return await self._call_in_executor(*args, **kwargs)


class BedrockChatProvider(BaseProvider, BedrockChat):
    id = "bedrock-chat"
    name = "Amazon Bedrock Chat"
    models = [
        "anthropic.claude-v1",
        "anthropic.claude-v2",
        "anthropic.claude-instant-v1",
    ]
    model_id_key = "model_id"
    pypi_package_deps = ["boto3"]
    auth_strategy = AwsAuthStrategy()
    fields = [
        TextField(
            key="credentials_profile_name",
            label="AWS profile (optional)",
            format="text",
        ),
        TextField(key="region_name", label="Region name (optional)", format="text"),
    ]

    async def _acall(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        return await self._call_in_executor(*args, **kwargs)

    async def _agenerate(self, *args, **kwargs) -> Coroutine[Any, Any, LLMResult]:
        return await self._generate_in_executor(*args, **kwargs)
