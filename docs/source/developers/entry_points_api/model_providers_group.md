# `'jupyter_ai.model_providers'`

```{contents} Contents
```

## Summary

This entry point group allows packages to add custom model providers.

This group expects a **model provider class**, a subclass of `BaseProvider` that
also inherits from a `LLM` or `ChatModel` class from LangChain. Instructions on
defining one are given in the next section.

:::{warning}
This is a v2 extension point that may be removed in v3. In v3, we may explore
updating the model API to make it easier for developers to add custom models.
:::

## How-to: Define a custom model provider

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

To make the new provider available, you need to declare it as an [entry point][entry_points]:

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

### Adding custom API keys and fields

You can add handle authentication via API keys, and configuration with
custom parameters using an auth strategy and fields as shown in the example
below.

```python
from typing import ClassVar, List
from jupyter_ai_magics import BaseProvider
from jupyter_ai_magics.providers import EnvAuthStrategy, Field, TextField, MultilineTextField
from langchain_community.llms import FakeListLLM


class MyProvider(BaseProvider, FakeListLLM):
    id = "my_provider"
    name = "My Provider"
    model_id_key = "model"
    models = [
        "model_a",
        "model_b"
    ]

    auth_strategy = EnvAuthStrategy(
        name="MY_API_KEY", keyword_param="my_api_key_param"
    )

    fields: ClassVar[List[Field]] = [
        TextField(key="my_llm_parameter", label="The name for my_llm_parameter to show in the UI"),
        MultilineTextField(key="custom_config", label="Custom Json Config", format="json"),
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

The `auth_strategy` handles specifying API keys for providers and models.
The example shows the `EnvAuthStrategy` which takes the API key from the
environment variable with the name specified in `name` and be provided to the
model's `__init__` as a kwarg with the name specified in `keyword_param`.
This will also cause a field to be present in the configuration UI with the
`name` of the environment variable as the label.

Further configuration can be handled adding `fields` into the settings
dialogue for your custom model by specifying a list of fields as shown in
the example.  These will be passed into the `__init__` as kwargs, with the
key specified by the key in the field object. The label specified in the field
object determines the text shown in the configuration section of the user
interface.

## How-to: Define custom code completions

Any model provider derived from `BaseProvider` can be used as a completion provider.
However, some providers may benefit from customizing handling of completion requests.

There are two asynchronous methods which can be overridden in subclasses of `BaseProvider`:

- `generate_inline_completions`: takes a request (`InlineCompletionRequest`) and
returns `InlineCompletionReply`

- `stream_inline_completions`: takes a request and yields an initiating reply
(`InlineCompletionReply`) with `isIncomplete` set to `True` followed by
subsequent chunks (`InlineCompletionStreamChunk`)

When streaming all replies and chunks for given invocation of the
`stream_inline_completions()` method should include a constant and unique string
token identifying the stream. All chunks except for the last chunk for a given
item should have the `done` value set to `False`.

The following example demonstrates a custom implementation of the completion
provider with both a method for sending multiple completions in one go, and
streaming multiple completions concurrently. The implementation and explanation
for the `merge_iterators` function used in this example can be found
[here](https://stackoverflow.com/q/72445371/4877269).

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

### Using the full notebook content for completions

The `InlineCompletionRequest` contains the `path` of the current document (file or notebook).
Inline completion providers can use this path to extract the content of the notebook from the disk,
however such content may be outdated if the user has not saved the notebook recently.

The accuracy of the suggestions can be slightly improved by combining the potentially outdated content of previous/following cells
with the `prefix` and `suffix` which describe the up-to-date state of the current cell (identified by `cell_id`).

Still, reading the full notebook from the disk may be slow for larger notebooks, which conflicts with the low latency requirement of inline completion.

A better approach is to use the live copy of the notebook document that is persisted on the jupyter-server when *collaborative* document models are enabled.
Two packages need to be installed to access the collaborative models:
- `jupyter-server-ydoc` (>= 1.0) stores the collaborative models in the jupyter-server on runtime
- `jupyter-docprovider` (>= 1.0) reconfigures JupyterLab/Notebook to use the collaborative models

Both packages are automatically installed with `jupyter-collaboration` (in v3.0 or newer), however installing `jupyter-collaboration` is not required to take advantage of *collaborative* models.

The snippet below demonstrates how to retrieve the content of all cells of a given type from the in-memory copy of the collaborative model (without additional disk reads).

```python
from jupyter_ydoc import YNotebook


class MyCompletionProvider(BaseProvider, FakeListLLM):
    id = "my_provider"
    name = "My Provider"
    model_id_key = "model"
    models = ["model_a"]

    def __init__(self, **kwargs):
        kwargs["responses"] = ["This fake response will not be used for completion"]
        super().__init__(**kwargs)

    async def _get_prefix_and_suffix(self, request: InlineCompletionRequest):
        prefix = request.prefix
        suffix = request.suffix.strip()

        server_ydoc = self.server_settings.get("jupyter_server_ydoc", None)
        if not server_ydoc:
            # fallback to prefix/suffix from single cell
            return prefix, suffix

        is_notebook = request.path.endswith("ipynb")
        document = await server_ydoc.get_document(
            path=request.path,
            content_type="notebook" if is_notebook else "file",
            file_format="json" if is_notebook else "text"
        )
        if not document or not isinstance(document, YNotebook):
            return prefix, suffix

        cell_type = "markdown" if request.language == "markdown" else "code"

        is_before_request_cell = True
        before = []
        after = [suffix]

        for cell in document.ycells:
            if is_before_request_cell and cell["id"] == request.cell_id:
                is_before_request_cell = False
                continue
            if cell["cell_type"] != cell_type:
                continue
            source = cell["source"].to_py()
            if is_before_request_cell:
                before.append(source)
            else:
                after.append(source)

        before.append(prefix)
        prefix = "\n\n".join(before)
        suffix = "\n\n".join(after)
        return prefix, suffix

    async def generate_inline_completions(self, request: InlineCompletionRequest):
        prefix, suffix = await self._get_prefix_and_suffix(request)

        return InlineCompletionReply(
            list=InlineCompletionList(items=[
                {"insertText": your_llm_function(prefix, suffix)}
            ]),
            reply_to=request.number,
        )
```

[entry_points]: https://setuptools.pypa.io/en/latest/userguide/entry_point.html
[langchain_llms]: https://api.python.langchain.com/en/v0.0.339/api_reference.html#module-langchain.llms
[custom_llm]: https://python.langchain.com/docs/modules/model_io/models/llms/custom_llm
[LLM]: https://api.python.langchain.com/en/v0.0.339/llms/langchain.llms.base.LLM.html#langchain.llms.base.LLM
[BaseChatModel]: https://api.python.langchain.com/en/v0.0.339/chat_models/langchain.chat_models.base.BaseChatModel.html
