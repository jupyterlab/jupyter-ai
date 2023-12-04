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
from langchain.llms import FakeListLLM


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
