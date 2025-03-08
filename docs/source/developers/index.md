# Developers

The developer documentation is for authors who want to enhance
the functionality of Jupyter AI.

If you are interested in contributing to Jupyter AI,
please see our {doc}`contributor's guide </contributors/index>`.

## Pydantic compatibility

- `jupyter-ai<2.29.0` requires Pydantic v1 **or** v2, but only supports
LangChain v0.2, which is now outdated.

    - Internally, `jupyter-ai<2.29.0` uses the Pydantic v1 API through a
    vendored module provided by LangChain. Therefore, if you are developing
    extensions for `jupyter-ai<2.29.0`, you should import Pydantic objects (e.g.
    `BaseModel`) from the `langchain.pydantic_v1` module. In this context, you
    should *not* use the `pydantic` module (as it may be Pydantic v1 or v2).

- `jupyter-ai>=2.29.0` requires Pydantic v2 (**not** v1), but supports LangChain
`>=0.3`.

    - Internally, `jupyter-ai>=2.29.0` uses the Pydantic v2 API directly through
    the `pydantic` module. Therefore, if you are developing extensions for
    `jupyter-ai>=2.29.0`, you should import Pydantic objects (e.g. `BaseModel`)
    from the `pydantic` module.

    - For context, LangChain v0.3 requires Pydantic v2. This motivated the
    upgrade to the Pydantic v2 API.

For more details about Pydantic & LangChain version compatibility, see the
[LangChain documentation on Pydantic compatibility](https://python.langchain.com/docs/how_to/pydantic_compatibility/).

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

### API keys and fields for custom providers

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


#### Using the full notebook content for completions

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

## Overriding or disabling a built-in slash command

You can define a custom implementation of a built-in slash command by following the steps above on building a custom slash command. This will involve creating and installing a new package. Then, to override a chat handler with this custom implementation, provide an entry point with a name matching the ID of the chat handler to override.

For example, to override `/ask` with a  `CustomAskChatHandler` class, add the following to `pyproject.toml` and re-install the new package:

```python
[project.entry-points."jupyter_ai.chat_handlers"]
ask = "<module-path>:CustomAskChatHandler"
```

You can also disable a built-in slash command by providing a mostly-empty chat handler with `disabled = True`. For example, to disable the default `ask` chat handler of Jupyter AI, define a new `DisabledAskChatHandler`:

```python
class DisabledAskChatHandler:
    id = 'ask'
    disabled = True
```

Then, provide this as an entry point in your custom package:
```python
[project.entry-points."jupyter_ai.chat_handlers"]
ask = "<module-path>:DisabledAskChatHandler"
```

Finally, re-install your custom package. After starting JupyterLab, the `/ask` command should now be disabled.

:::{warning}
:name: entry-point-name
To override or disable a built-in slash command via an entry point, the name of the entry point (left of the `=` symbol) must match the chat handler ID exactly.
:::

## Streaming output from custom slash commands

Jupyter AI supports streaming output in the chat session. When a response is
streamed to the user, the user can watch the response being constructed in
real-time, which offers a visually pleasing user experience. Custom slash
commands can stream responses in chat by invoking the `stream_reply()` method,
provided by the `BaseChatHandler` class that custom slash commands inherit from.
Custom slash commands should always use `self.stream_reply()` to stream
responses, as it provides support for stopping the response stream from the UI.

To use `stream_reply()`, your slash command must bind a LangChain
[`Runnable`](https://python.langchain.com/api_reference/core/runnables/langchain_core.runnables.base.Runnable.html)
to `self.llm_chain` in the `create_llm_chain()` method. Runnables can be created
by using LangChain Expression Language (LCEL). See below for an example
definition of `create_llm_chain()`, sourced from our implementation of `/fix` in
`fix.py`:

```python
def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        unified_parameters = {
            "verbose": True,
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        llm = provider(**unified_parameters)
        self.llm = llm
        prompt_template = FIX_PROMPT_TEMPLATE
        self.prompt_template = prompt_template

        runnable = prompt_template | llm | StrOutputParser()  # type:ignore
        self.llm_chain = runnable
```

Once your chat handler binds a Runnable to `self.llm_chain` in
`self.create_llm_chain()`, you can define `process_message()` to invoke
`self.stream_reply()`, which streams a reply back to the user using
`self.llm_chain.astream()`.
`self.stream_reply()` has two required arguments:

- `input`: An input to your LangChain Runnable. This is usually a dictionary
whose keys are input variables specified in your prompt template, but may be
just a string if your Runnable does not use a prompt template.

- `message`: The `HumanChatMessage` being replied to.

An example of `process_message()` can also be sourced from our implementation of `/fix`:

```python
async def process_message(self, message: HumanChatMessage):
        if not (message.selection and message.selection.type == "cell-with-error"):
            self.reply(
                "`/fix` requires an active code cell with error output. Please click on a cell with error output and retry.",
                message,
            )
            return

        # hint type of selection
        selection: CellWithErrorSelection = message.selection

        # parse additional instructions specified after `/fix`
        extra_instructions = message.prompt[4:].strip() or "None."

        self.get_llm_chain()
        assert self.llm_chain

        inputs = {
            "extra_instructions": extra_instructions,
            "cell_content": selection.source,
            "traceback": selection.error.traceback,
            "error_name": selection.error.name,
            "error_value": selection.error.value,
        }
        await self.stream_reply(inputs, message, pending_msg="Analyzing error")
```

The last line of `process_message` above calls `stream_reply` in `base.py`.
Note that a custom pending message may also be passed.
The `stream_reply` function leverages the LCEL Runnable.
The function takes in the input, human message, and optional
pending message strings and configuration, as shown below:

```python
async def stream_reply(
        self,
        input: Input,
        human_msg: HumanChatMessage,
        pending_msg="Generating response",
        config: Optional[RunnableConfig] = None,
    ):
        """
        Streams a reply to a human message by invoking
        `self.llm_chain.astream()`. A LangChain `Runnable` instance must be
        bound to `self.llm_chain` before invoking this method.

        Arguments
        ---------
        - `input`: The input to your runnable. The type of `input` depends on
        the runnable in `self.llm_chain`, but is usually a dictionary whose keys
        refer to input variables in your prompt template.

        - `human_msg`: The `HumanChatMessage` being replied to.

        - `config` (optional): A `RunnableConfig` object that specifies
        additional configuration when streaming from the runnable.

        - `pending_msg` (optional): Changes the default pending message from
        "Generating response".
        """
        assert self.llm_chain
        assert isinstance(self.llm_chain, Runnable)
```

## Custom message footer

You can provide a custom message footer that will be rendered under each message
in the UI. To do so, you need to write or install a labextension containing a
plugin that provides the `IJaiMessageFooter` token. This plugin should return a
`IJaiMessageFooter` object, which defines the custom footer to be rendered.

The `IJaiMessageFooter` object contains a single property `component`, which
should reference a React component that defines the custom message footer.
Jupyter AI will render this component under each chat message, passing the
component a `message` prop with the definition of each chat message as an
object. The `message` prop takes the type `AiService.ChatMessage`, where
`AiService` is imported from `@jupyter-ai/core/handler`.

Here is a reference plugin that shows some custom text under each agent message:

```tsx
import React from 'react';
import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { IJaiMessageFooter, IJaiMessageFooterProps } from '@jupyter-ai/core/tokens';

export const footerPlugin: JupyterFrontEndPlugin<IJaiMessageFooter> = {
  id: '@your-org/your-package:custom-footer',
  autoStart: true,
  requires: [],
  provides: IJaiMessageFooter,
  activate: (app: JupyterFrontEnd): IJaiMessageFooter => {
    return {
      component: MessageFooter
    };
  }
};

function MessageFooter(props: IJaiMessageFooterProps) {
  if (props.message.type !== 'agent' && props.message.type !== 'agent-stream') {
    return null;
  }

  return (
    <div>This is a test footer that renders under each agent message.</div>
  );
}
```
