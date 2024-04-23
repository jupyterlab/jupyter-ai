# Developers

The developer documentation is for authors who want to enhance
the functionality of Jupyter AI.

If you are interested in contributing to Jupyter AI,
please see our {doc}`contributor's guide </contributors/index>`.

## Pydantic compatibility

Jupyter AI is fully compatible with Python environments using Pydantic v1
or Pydantic v2. Jupyter AI imports Pydantic classes from the
`langchain.pydantic_v1` module. Developers should do the same when they extend
Jupyter AI classes.

For more details about using `langchain.pydantic_v1` in an environment with
Pydantic v2 installed, see the
[LangChain documentation on Pydantic compatibility](https://python.langchain.com/docs/guides/pydantic_compatibility).

## Jupyter AI module cookiecutter

We offer a [cookiecutter](https://github.com/cookiecutter/cookiecutter) template
that can be used to generate a pre-configured Jupyter AI module. This is a
Python package that exposes a template model provider and slash command for
integration with Jupyter AI. Developers can then extend the generated AI module
however they wish.

To generate a new AI module using the cookiecutter, run these commands from the
repository root:

```
pip install cookiecutter
cd packages/
cookiecutter jupyter-ai-module-cookiecutter
```

The last command will open a wizard that allows you to set the package name and
a few other metadata fields. By default, the package will have the name `jupyter-ai-test`.

To install your new AI module locally and use the generated template provider
and slash command:

```
cd jupyter-ai-test/
pip install -e .
```

You will then be able to use the test provider and slash command after
restarting JupyterLab.

The remainder of this documentation page elaborates on how to define a custom
model provider and slash command.

## Custom model providers

You can define new providers using the LangChain framework API. Custom providers
inherit from both `jupyter-ai`'s `BaseProvider` and `langchain`'s [`LLM`][LLM].
You can either import a pre-defined model from [LangChain LLM list][langchain_llms],
or define a [custom LLM][custom_llm].
In the example below, we define a provider with two models using
a dummy `FakeListLLM` model, which returns responses from the `responses`
keyword argument.

```python
# my_package/my_provider.py
from jupyter_ai_magics import BaseProvider
from langchain_community.llms import FakeListLLM


class MyProvider(BaseProvider, FakeListLLM):
    id = "my_provider"
    name = "My Provider"
    model_id_key = "model"
    models = [
        "model_a",
        "model_b"
    ]
    def __init__(self, **kwargs):
        model = kwargs.get("model_id")
        kwargs["responses"] = (
            ["This is a response from model 'a'"]
            if model == "model_a" else
            ["This is a response from model 'b'"]
        )
        super().__init__(**kwargs)
```


If the new provider inherits from [`BaseChatModel`][BaseChatModel], it will be available
both in the chat UI and with magic commands. Otherwise, users can only use the new provider
with magic commands.

To make the new provider available, you need to declare it as an [entry point](https://setuptools.pypa.io/en/latest/userguide/entry_point.html):

```toml
# my_package/pyproject.toml
[project]
name = "my_package"
version = "0.0.1"

[project.entry-points."jupyter_ai.model_providers"]
my-provider = "my_provider:MyProvider"
```

To test that the above minimal provider package works, install it with:

```sh
# from `my_package` directory
pip install -e .
```

Then, restart JupyterLab. You should now see an info message in the log that mentions
your new provider's `id`:

```
[I 2023-10-29 13:56:16.915 AiExtension] Registered model provider `my_provider`.
```

[langchain_llms]: https://api.python.langchain.com/en/v0.0.339/api_reference.html#module-langchain.llms
[custom_llm]: https://python.langchain.com/docs/modules/model_io/models/llms/custom_llm
[LLM]: https://api.python.langchain.com/en/v0.0.339/llms/langchain.llms.base.LLM.html#langchain.llms.base.LLM
[BaseChatModel]: https://api.python.langchain.com/en/v0.0.339/chat_models/langchain.chat_models.base.BaseChatModel.html

### Custom embeddings providers

To provide a custom embeddings model an embeddings providers should be defined implementing the API of `jupyter-ai`'s `BaseEmbeddingsProvider` and of `langchain`'s [`Embeddings`][Embeddings] abstract class.

```python
from jupyter_ai_magics import BaseEmbeddingsProvider
from langchain.embeddings import FakeEmbeddings

class MyEmbeddingsProvider(BaseEmbeddingsProvider, FakeEmbeddings):
    id = "my_embeddings_provider"
    name = "My Embeddings Provider"
    model_id_key = "model"
    models = ["my_model"]

    def __init__(self, **kwargs):
        super().__init__(size=300, **kwargs)
```

Jupyter AI uses entry points to discover embedding providers.
In the `pyproject.toml` file, add your custom embedding provider to the
`[project.entry-points."jupyter_ai.embeddings_model_providers"]` section:

```toml
[project.entry-points."jupyter_ai.embeddings_model_providers"]
my-provider = "my_provider:MyEmbeddingsProvider"
```

[Embeddings]: https://api.python.langchain.com/en/stable/embeddings/langchain_core.embeddings.Embeddings.html


### Custom completion providers

Any model provider derived from `BaseProvider` can be used as a completion provider.
However, some providers may benefit from customizing handling of completion requests.

There are two asynchronous methods which can be overridden in subclasses of `BaseProvider`:
- `generate_inline_completions`: takes a request (`InlineCompletionRequest`) and returns `InlineCompletionReply`
- `stream_inline_completions`: takes a request and yields an initiating reply (`InlineCompletionReply`) with `isIncomplete` set to `True` followed by subsequent chunks (`InlineCompletionStreamChunk`)

When streaming all replies and chunks for given invocation of the `stream_inline_completions()` method should include a constant and unique string token identifying the stream. All chunks except for the last chunk for a given item should have the `done` value set to `False`.

The following example demonstrates a custom implementation of the completion provider with both a method for sending multiple completions in one go, and streaming multiple completions concurrently.
The implementation and explanation for the `merge_iterators` function used in this example can be found [here](https://stackoverflow.com/q/72445371/4877269).

```python
class MyCompletionProvider(BaseProvider, FakeListLLM):
    id = "my_provider"
    name = "My Provider"
    model_id_key = "model"
    models = ["model_a"]

    def __init__(self, **kwargs):
        kwargs["responses"] = ["This fake response will not be used for completion"]
        super().__init__(**kwargs)

    async def generate_inline_completions(self, request: InlineCompletionRequest):
        return InlineCompletionReply(
            list=InlineCompletionList(items=[
                {"insertText": "An ant minding its own business"},
                {"insertText": "A bug searching for a snack"}
            ]),
            reply_to=request.number,
        )

    async def stream_inline_completions(self, request: InlineCompletionRequest):
        token_1 = f"t{request.number}s0"
        token_2 = f"t{request.number}s1"

        yield InlineCompletionReply(
            list=InlineCompletionList(
                items=[
                    {"insertText": "An ", "isIncomplete": True, "token": token_1},
                    {"insertText": "", "isIncomplete": True, "token": token_2}
                ]
            ),
            reply_to=request.number,
        )

        # where merge_iterators
        async for reply in merge_iterators([
            self._stream("elephant dancing in the rain", request.number, token_1, start_with="An"),
            self._stream("A flock of birds flying around a mountain", request.number, token_2)
        ]):
            yield reply

    async def _stream(self, sentence, request_number, token, start_with = ""):
        suggestion = start_with

        for fragment in sentence.split():
            await asyncio.sleep(0.75)
            suggestion += " " + fragment
            yield InlineCompletionStreamChunk(
                type="stream",
                response={"insertText": suggestion, "token": token},
                reply_to=request_number,
                done=False
            )

        # finally, send a message confirming that we are done
        yield InlineCompletionStreamChunk(
            type="stream",
            response={"insertText": suggestion, "token": token},
            reply_to=request_number,
            done=True,
        )
```

## Prompt templates

Each provider can define **prompt templates** for each supported format. A prompt
template guides the language model to produce output in a particular
format. The default prompt templates are a
[Python dictionary mapping formats to templates](https://github.com/jupyterlab/jupyter-ai/blob/57a758fa5cdd5a87da5519987895aa688b3766a8/packages/jupyter-ai-magics/jupyter_ai_magics/providers.py#L138-L166).
Developers who write subclasses of `BaseProvider` can override templates per
output format, per model, and based on the prompt being submitted, by
implementing their own
[`get_prompt_template` function](https://github.com/jupyterlab/jupyter-ai/blob/57a758fa5cdd5a87da5519987895aa688b3766a8/packages/jupyter-ai-magics/jupyter_ai_magics/providers.py#L186-L195).
Each prompt template includes the string `{prompt}`, which is replaced with
the user-provided prompt when the user runs a magic command.

### Customizing prompt templates

To modify the prompt template for a given format, override the `get_prompt_template` method:

```python
from langchain.prompts import PromptTemplate


class MyProvider(BaseProvider, FakeListLLM):
    # (... properties as above ...)
    def get_prompt_template(self, format) -> PromptTemplate:
        if format === "code":
            return PromptTemplate.from_template(
                "{prompt}\n\nProduce output as source code only, "
                "with no text or explanation before or after it."
            )
        return super().get_prompt_template(format)
```

Please note that this will only work with Jupyter AI magics (the `%ai` and `%%ai` magic commands). Custom prompt templates are not used in the chat interface yet.

## Custom slash commands in the chat UI

You can add a custom slash command to the chat interface by
creating a new class that inherits from `BaseChatHandler`. Set
its `id`, `name`, `help` message for display in the user interface,
and `routing_type`. Each custom slash command must have a unique
slash command. Slash commands can only contain ASCII letters, numerals,
and underscores. Each slash command must be unique; custom slash
commands cannot replace built-in slash commands.

Add your custom handler in Python code:

```python
from jupyter_ai.chat_handlers.base import BaseChatHandler, SlashCommandRoutingType
from jupyter_ai.models import HumanChatMessage

class CustomChatHandler(BaseChatHandler):
    id = "custom"
    name = "Custom"
    help = "A chat handler that does something custom"
    routing_type = SlashCommandRoutingType(slash_id="custom")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def process_message(self, message: HumanChatMessage):
        # Put your custom logic here
        self.reply("<your-response>", message)
```

Jupyter AI uses entry points to support custom slash commands.
In the `pyproject.toml` file, add your custom handler to the
`[project.entry-points."jupyter_ai.chat_handlers"]` section:

```toml
[project.entry-points."jupyter_ai.chat_handlers"]
custom = "custom_package:CustomChatHandler"
```

Then, install your package so that Jupyter AI adds custom chat handlers
to the existing chat handlers.
