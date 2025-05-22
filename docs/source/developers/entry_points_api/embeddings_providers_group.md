# `'jupyter_ai.embeddings_model_providers'`

```{contents} Contents
```

## Summary

This entry point group allows packages to add custom embedding model providers
to power the retrieval-augmented generation (RAG) capabilities of Jupyter AI.

This group expects an **embedding model provider class**, a subclass of
`BaseEmbeddingsProvider` from `jupyter-ai` that also inherits from an
`Embeddings` class from LangChain. Instructions on defining one are given in the
next section.

:::{warning}
This is a v2 extension point that may be removed in v3. In v3, we may explore
updating the model API to make it easier for developers to add custom models.
:::

## How-to: define a custom embedding model provider

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
