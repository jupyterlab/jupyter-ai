import asyncio
import base64
import functools
import io
import json
from concurrent.futures import ThreadPoolExecutor
from types import MappingProxyType
from typing import (
    Any,
    AsyncIterator,
    ClassVar,
    Coroutine,
    Dict,
    List,
    Literal,
    Optional,
    Union,
)

from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.pydantic_v1 import BaseModel, Extra
from langchain.schema import LLMResult
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain_community.chat_models import QianfanChatEndpoint
from langchain_community.llms import AI21, GPT4All, HuggingFaceEndpoint, Together
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.llms import BaseLLM

# this is necessary because `langchain.pydantic_v1.main` does not include
# `ModelMetaclass`, as it is not listed in `__all__` by the `pydantic.main`
# subpackage.
try:
    from pydantic.v1.main import ModelMetaclass
except:
    from pydantic.main import ModelMetaclass

from . import completion_utils as completion
from .models.completion import (
    InlineCompletionList,
    InlineCompletionReply,
    InlineCompletionRequest,
    InlineCompletionStreamChunk,
)
from .models.persona import Persona

CHAT_SYSTEM_PROMPT = """
You are Jupyternaut, a conversational assistant living in JupyterLab to help users.
You are not a language model, but rather an application built on a foundation model from {provider_name} called {local_model_id}.
You are talkative and you provide lots of specific details from the foundation model's context.
You may use Markdown to format your response.
Code blocks must be formatted in Markdown.
Math should be rendered with inline TeX markup, surrounded by $.
If you do not know the answer to a question, answer truthfully by responding that you do not know.
The following is a friendly conversation between you and a human.
""".strip()

CHAT_DEFAULT_TEMPLATE = """
{% if context %}
Context:
{{context}}

{% endif %}
Current conversation:
{{history}}
Human: {{input}}
AI:"""

HUMAN_MESSAGE_TEMPLATE = """
{% if context %}
Context:
{{context}}

{% endif %}
{{input}}
"""

COMPLETION_SYSTEM_PROMPT = """
You are an application built to provide helpful code completion suggestions.
You should only produce code. Keep comments to minimum, use the
programming language comment syntax. Produce clean code.
The code is written in JupyterLab, a data analysis and code development
environment which can execute code extended with additional syntax for
interactive features, such as magics.
""".strip()

# only add the suffix bit if present to save input tokens/computation time
COMPLETION_DEFAULT_TEMPLATE = """
The document is called `{{filename}}` and written in {{language}}.
{% if suffix %}
The code after the completion request is:

```
{{suffix}}
```
{% endif %}

Complete the following code:

```
{{prefix}}"""


class EnvAuthStrategy(BaseModel):
    """
    Describes a provider that uses a single authentication token, which is
    passed either as an environment variable or as a keyword argument.
    """

    type: Literal["env"] = "env"

    name: str
    """The name of the environment variable, e.g. `'ANTHROPIC_API_KEY'`."""

    keyword_param: Optional[str]
    """
    If unset (default), the authentication token is provided as a keyword
    argument with the parameter equal to the environment variable name in
    lowercase. If set to some string `k`, the authentication token will be
    passed using the keyword parameter `k`.
    """


class MultiEnvAuthStrategy(BaseModel):
    """Require multiple auth tokens via multiple environment variables."""

    type: Literal["multienv"] = "multienv"
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


class ProviderMetaclass(ModelMetaclass):
    """
    A metaclass that ensures all class attributes defined inline within the
    class definition are accessible and included in `Class.__dict__`.

    This is necessary because Pydantic drops any ClassVars that are defined as
    an instance field by a parent class, even if they are defined inline within
    the class definition. We encountered this case when `langchain` added a
    `name` attribute to a parent class shared by all `Provider`s, which caused
    `Provider.name` to be inaccessible. See #558 for more info.
    """

    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        for key in namespace:
            # skip private class attributes
            if key.startswith("_"):
                continue
            # skip class attributes already listed in `cls.__dict__`
            if key in cls.__dict__:
                continue

            setattr(cls, key, namespace[key])

        return cls

    @property
    def server_settings(cls):
        return cls._server_settings

    @server_settings.setter
    def server_settings(cls, value):
        if cls._server_settings is not None:
            raise AttributeError("'server_settings' attribute was already set")
        cls._server_settings = value

    _server_settings = None


class BaseProvider(BaseModel, metaclass=ProviderMetaclass):
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

    manages_history: ClassVar[bool] = False
    """Whether this provider manages its own conversation history upstream. If
    set to `True`, Jupyter AI will not pass the chat history to this provider
    when invoked."""

    persona: ClassVar[Optional[Persona]] = None
    """
    The **persona** of this provider, a struct that defines the name and avatar
    shown on agent replies in the chat UI. When set to `None`, `jupyter-ai` will
    choose a default persona when rendering agent messages by this provider.

    Because this field is set to `None` by default, `jupyter-ai` will render a
    default persona for all providers that are included natively with the
    `jupyter-ai` package. This field is reserved for Jupyter AI modules that
    serve a custom provider and want to distinguish it in the chat UI.
    """

    unsupported_slash_commands: ClassVar[set] = set()
    """
    A set of slash commands unsupported by this provider. Unsupported slash
    commands are not shown in the help message, and cannot be used while this
    provider is selected.
    """

    server_settings: ClassVar[Optional[MappingProxyType]] = None
    """Settings passed on from jupyter-ai package.

    The same server settings are shared between all providers.
    Providers are not allowed to mutate this dictionary.
    """

    @classmethod
    def chat_models(self):
        """Models which are suitable for chat."""
        return self.models

    @classmethod
    def completion_models(self):
        """Models which are suitable for completions."""
        return self.models

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

    @classmethod
    def is_api_key_exc(cls, _: Exception):
        """
        Determine if the exception is an API key error. Can be implemented by subclasses.
        """
        return False

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

    def get_chat_prompt_template(self) -> PromptTemplate:
        """
        Produce a prompt template optimised for chat conversation.
        The template should take two variables: history and input.
        """
        name = self.__class__.name
        if self.is_chat_provider:
            return ChatPromptTemplate.from_messages(
                [
                    SystemMessagePromptTemplate.from_template(
                        CHAT_SYSTEM_PROMPT
                    ).format(provider_name=name, local_model_id=self.model_id),
                    MessagesPlaceholder(variable_name="history"),
                    HumanMessagePromptTemplate.from_template(
                        HUMAN_MESSAGE_TEMPLATE,
                        template_format="jinja2",
                    ),
                ]
            )
        else:
            return PromptTemplate(
                input_variables=["history", "input", "context"],
                template=CHAT_SYSTEM_PROMPT.format(
                    provider_name=name, local_model_id=self.model_id
                )
                + "\n\n"
                + CHAT_DEFAULT_TEMPLATE,
                template_format="jinja2",
            )

    def get_completion_prompt_template(self) -> PromptTemplate:
        """
        Produce a prompt template optimised for inline code or text completion.
        The template should take variables: prefix, suffix, language, filename.
        """
        if self.is_chat_provider:
            return ChatPromptTemplate.from_messages(
                [
                    SystemMessagePromptTemplate.from_template(COMPLETION_SYSTEM_PROMPT),
                    HumanMessagePromptTemplate.from_template(
                        COMPLETION_DEFAULT_TEMPLATE, template_format="jinja2"
                    ),
                ]
            )
        else:
            return PromptTemplate(
                input_variables=["prefix", "suffix", "language", "filename"],
                template=COMPLETION_SYSTEM_PROMPT
                + "\n\n"
                + COMPLETION_DEFAULT_TEMPLATE,
                template_format="jinja2",
            )

    @property
    def is_chat_provider(self):
        return isinstance(self, BaseChatModel)

    @property
    def allows_concurrency(self):
        return True

    @property
    def _supports_sync_streaming(self):
        if self.is_chat_provider:
            return not (self.__class__._stream is BaseChatModel._stream)
        else:
            return not (self.__class__._stream is BaseLLM._stream)

    @property
    def _supports_async_streaming(self):
        if self.is_chat_provider:
            return not (self.__class__._astream is BaseChatModel._astream)
        else:
            return not (self.__class__._astream is BaseLLM._astream)

    @property
    def supports_streaming(self):
        return self._supports_sync_streaming or self._supports_async_streaming

    async def generate_inline_completions(
        self, request: InlineCompletionRequest
    ) -> InlineCompletionReply:
        chain = self._create_completion_chain()
        model_arguments = completion.template_inputs_from_request(request)
        suggestion = await chain.ainvoke(input=model_arguments)
        suggestion = completion.post_process_suggestion(suggestion, request)
        return InlineCompletionReply(
            list=InlineCompletionList(items=[{"insertText": suggestion}]),
            reply_to=request.number,
        )

    async def stream_inline_completions(
        self, request: InlineCompletionRequest
    ) -> AsyncIterator[InlineCompletionStreamChunk]:
        chain = self._create_completion_chain()
        token = completion.token_from_request(request, 0)
        model_arguments = completion.template_inputs_from_request(request)
        suggestion = processed_suggestion = ""

        # send an incomplete `InlineCompletionReply`, indicating to the
        # client that LLM output is about to streamed across this connection.
        yield InlineCompletionReply(
            list=InlineCompletionList(
                items=[
                    {
                        # insert text starts empty as we do not pre-generate any part
                        "insertText": "",
                        "isIncomplete": True,
                        "token": token,
                    }
                ]
            ),
            reply_to=request.number,
        )

        async for fragment in chain.astream(input=model_arguments):
            suggestion += fragment
            processed_suggestion = completion.post_process_suggestion(
                suggestion, request
            )
            yield InlineCompletionStreamChunk(
                type="stream",
                response={"insertText": processed_suggestion, "token": token},
                reply_to=request.number,
                done=False,
            )

        # finally, send a message confirming that we are done
        yield InlineCompletionStreamChunk(
            type="stream",
            response={"insertText": processed_suggestion, "token": token},
            reply_to=request.number,
            done=True,
        )

    def _create_completion_chain(self) -> Runnable:
        prompt_template = self.get_completion_prompt_template()
        return prompt_template | self | StrOutputParser()


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

    @classmethod
    def is_api_key_exc(cls, e: Exception):
        """
        Determine if the exception is an AI21 API key error.
        """
        if isinstance(e, ValueError):
            return "status code 401" in str(e)
        return False


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
        "mistral-7b-openorca.Q4_0",
        "mistral-7b-instruct-v0.1.Q4_0",
        "gpt4all-falcon-q4_0",
        "wizardlm-13b-v1.2.Q4_0",
        "nous-hermes-llama2-13b.Q4_0",
        "gpt4all-13b-snoozy-q4_0",
        "mpt-7b-chat-merges-q4_0",
        "orca-mini-3b-gguf2-q4_0",
        "starcoder-q4_0",
        "rift-coder-v0-7b-q4_0",
        "em_german_mistral_v01.Q4_0",
    ]
    model_id_key = "model"
    pypi_package_deps = ["gpt4all"]
    auth_strategy = None
    fields = [IntegerField(key="n_threads", label="CPU thread count (optional)")]

    async def _acall(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        return await self._call_in_executor(*args, **kwargs)

    @property
    def allows_concurrency(self):
        # At present, GPT4All providers fail with concurrent messages. See #481.
        return False


# References for using HuggingFaceEndpoint and InferenceClient:
# https://huggingface.co/docs/huggingface_hub/main/en/package_reference/inference_client#huggingface_hub.InferenceClient
# https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/llms/huggingface_endpoint.py
class HfHubProvider(BaseProvider, HuggingFaceEndpoint):
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

    # Handle text and image outputs
    def _call(
        self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any
    ) -> str:
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
        invocation_params = self._invocation_params(stop, **kwargs)
        invocation_params["stop"] = invocation_params[
            "stop_sequences"
        ]  # porting 'stop_sequences' into the 'stop' argument
        response = self.client.post(
            json={"inputs": prompt, "parameters": invocation_params},
            stream=False,
            task=self.task,
        )

        try:
            if "generated_text" in str(response):
                # text2 text or text-generation task
                response_text = json.loads(response.decode())[0]["generated_text"]
                # Maybe the generation has stopped at one of the stop sequences:
                # then we remove this stop sequence from the end of the generated text
                for stop_seq in invocation_params["stop_sequences"]:
                    if response_text[-len(stop_seq) :] == stop_seq:
                        response_text = response_text[: -len(stop_seq)]
                return response_text
            else:
                # text-to-image task
                # https://huggingface.co/docs/huggingface_hub/main/en/package_reference/inference_client#huggingface_hub.InferenceClient.text_to_image.example
                # Custom code for responding to image generation responses
                image = self.client.text_to_image(prompt)
                imageFormat = image.format  # Presume it's a PIL ImageFile
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
                image.save(buffer, format=imageFormat)
                # # Encode image data to Base64 bytes, then decode bytes to str
                return (
                    mimeType + ";base64," + base64.b64encode(buffer.getvalue()).decode()
                )
        except:
            raise ValueError(
                "Task not supported, only text-generation and text-to-image tasks are valid."
            )

    async def _acall(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        return await self._call_in_executor(*args, **kwargs)


class TogetherAIProvider(BaseProvider, Together):
    id = "togetherai"
    name = "Together AI"
    model_id_key = "model"
    models = [
        "Austism/chronos-hermes-13b",
        "DiscoResearch/DiscoLM-mixtral-8x7b-v2",
        "EleutherAI/llemma_7b",
        "Gryphe/MythoMax-L2-13b",
        "Meta-Llama/Llama-Guard-7b",
        "Nexusflow/NexusRaven-V2-13B",
        "NousResearch/Nous-Capybara-7B-V1p9",
        "NousResearch/Nous-Hermes-2-Yi-34B",
        "NousResearch/Nous-Hermes-Llama2-13b",
        "NousResearch/Nous-Hermes-Llama2-70b",
    ]
    pypi_package_deps = ["together"]
    auth_strategy = EnvAuthStrategy(name="TOGETHER_API_KEY")

    def __init__(self, **kwargs):
        model = kwargs.get("model_id")

        if model not in self.models:
            kwargs["responses"] = [
                "Model not supported! Please check model list with %ai list"
            ]

        super().__init__(**kwargs)

    def get_prompt_template(self, format) -> PromptTemplate:
        if format == "code":
            return PromptTemplate.from_template(
                "{prompt}\n\nProduce output as source code only, "
                "with no text or explanation before or after it."
            )
        return super().get_prompt_template(format)


# Baidu QianfanChat provider. temporarily living as a separate class until
class QianfanProvider(BaseProvider, QianfanChatEndpoint):
    id = "qianfan"
    name = "ERNIE-Bot"
    models = ["ERNIE-Bot", "ERNIE-Bot-4"]
    model_id_key = "model_name"
    pypi_package_deps = ["qianfan"]
    auth_strategy = MultiEnvAuthStrategy(names=["QIANFAN_AK", "QIANFAN_SK"])
