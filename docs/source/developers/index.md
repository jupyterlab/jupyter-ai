# Developers

This section describes the **developer API** in Jupyter AI that other Python
packages can use to tailor Jupyter AI to their use-case. Here are some examples
of what other packages can do with the developer API:

- Add custom AI personas to Jupyter AI

- Add custom model providers to Jupyter AI

The developer API allows other packages to modify both the frontend & the
backend. The developer API has two parts: the **Entry points API** and the
**Lumino plugin API** (currently unused, but planned for v3).

- The Entry points API allows packages to add certain objects to Jupyter AI's
backend. This is available to any Python package.

- The Lumino plugin API allows packages to add to, modify, or even override
parts of Jupyter AI's frontend. This is only available to labextension packages.

## Entry points API

The [**entry points API**][entry_points] allows other packages to add custom
objects to Jupyter AI's backend. Jupyter AI defines a set of **entry point
groups**. Each entry point group is reserved for a specific type of object, e.g.
one group may be reserved for personas and another may be reserved for model
providers.

A package can *provide* an **entry point** to an entry point group to add an
object of the type reserved by the group. For example, providing an entry point
to the personas group will add a new AI persona to Jupyter AI. A package can
also provide multiple entry points to the same group.

The entry points API currently includes the following entry point groups:

- `'jupyter_ai.personas'`: allows developers to add AI personas.

- `'jupyter_ai.model_providers'`: allows developers to add model providers.

Each entry point group used by Jupyter AI is documented in a sub-section below,
which describes the type of object expected and how to define a custom
implementation.

At the end, we describe how to provide an entry point using a custom
implementation in your package.

### `'jupyter_ai.personas'`

WIP.

### `'jupyter_ai.model_providers'`

This entry point group allows packages to add custom model providers.

:::{warning}
This is a v2 extension point that may be removed in v3. In v3, we may explore
updating the model API to make it easier for developers to add custom models.
:::

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

### Providing entry points

To provide entry points, your custom Python package must use a `pyproject.toml`
manifest. To provide an existing class as an entry point, fill out the following
template and add it to the end of your package's
`pyproject.toml` file.

```
[project.entry-points.<entry-point-group>]
<some-unique-name> = "<module-path>:<class-name>"
```

where:

- `<entry-point-group>` takes the name of an entry point group used by Jupyter
AI, e.g. `'jupyter_ai.personas'`. Make sure `<entry-point-group>` is surrounded
by single or double quotes.

- `<some-unique-name>` can be any string, as long as it is unique within each
`[projects.entry-points.*]` table.

- `<module-path>` takes the path to your module containing the class.

    - For example, if you are providing a persona defined in
    `my_custom_package/personas/custom.py`, then this field should be set to
    `my_custom_package.personas.custom`.

- `<class-name>` takes the name of the class defined in `<module-path>`.

Finally, for Jupyter AI to read from your package's entry points, your package
must be installed in the same Python environment. Entry points are only read by
Jupyter AI when the server starts, so you should also restart JupyterLab after
installing your custom package to see the new changes.

:::{note}
After adding/removing an entry point, you will also need to re-install the
package & restart JupyterLab for the changes to take effect.
:::


[entry_points]: https://setuptools.pypa.io/en/latest/userguide/entry_point.html 
[langchain_llms]: https://api.python.langchain.com/en/v0.0.339/api_reference.html#module-langchain.llms
[custom_llm]: https://python.langchain.com/docs/modules/model_io/models/llms/custom_llm
[LLM]: https://api.python.langchain.com/en/v0.0.339/llms/langchain.llms.base.LLM.html#langchain.llms.base.LLM
[BaseChatModel]: https://api.python.langchain.com/en/v0.0.339/chat_models/langchain.chat_models.base.BaseChatModel.html
