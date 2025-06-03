import asyncio
import functools
from collections.abc import AsyncIterator, Coroutine
from concurrent.futures import ThreadPoolExecutor
from types import MappingProxyType
from typing import (
    Any,
    ClassVar,
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
from langchain.schema import LLMResult
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.llms import BaseLLM
from pydantic import BaseModel, ConfigDict

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
If your response includes code, they must be enclosed in Markdown fenced code blocks (with triple backticks before and after).
If your response includes mathematical notation, they must be expressed in LaTeX markup and enclosed in LaTeX delimiters.
All dollar quantities (of USD) must be formatted in LaTeX, with the `$` symbol escaped by a single backslash `\\`.
- Example prompt: `If I have \\\\$100 and spend \\\\$20, how much money do I have left?`
- **Correct** response: `You have \\(\\$80\\) remaining.`
- **Incorrect** response: `You have $80 remaining.`
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

    keyword_param: Optional[str] = None
    """
    If unset (default), the authentication token is provided as a keyword
    argument with the parameter equal to the environment variable name in
    lowercase. If set to some string `k`, the authentication token will be
    passed using the keyword parameter `k`.
    """


class MultiEnvAuthStrategy(BaseModel):
    """Require multiple auth tokens via multiple environment variables."""

    type: Literal["multienv"] = "multienv"
    names: list[str]


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
    # pydantic v2 model config
    # upstream docs: https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra
    model_config = ConfigDict(extra="allow")

    #
    # class attrs
    #
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

    model_id_key: ClassVar[Optional[str]] = None
    """
    Optional field which specifies the key under which `model_id` is passed to
    the parent LangChain class.

    If unset, this defaults to "model_id".
    """

    model_id_label: ClassVar[Optional[str]] = None
    """
    Optional field which sets the label shown in the UI allowing users to
    select/type a model ID.

    If unset, the label shown in the UI defaults to "Model ID".
    """

    pypi_package_deps: ClassVar[list[str]] = []
    """List of PyPi package dependencies."""

    auth_strategy: ClassVar[AuthStrategy] = None
    """Authentication/authorization strategy. Declares what credentials are
    required to use this model provider. Generally should not be `None`."""

    registry: ClassVar[bool] = False
    """Whether this provider is a registry provider."""

    fields: ClassVar[list[Field]] = []
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
    prompt_templates: dict[str, PromptTemplate]
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
