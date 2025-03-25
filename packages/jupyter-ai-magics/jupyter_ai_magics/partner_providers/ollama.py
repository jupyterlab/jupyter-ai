from langchain_ollama import ChatOllama, OllamaEmbeddings

from ..embedding_providers import BaseEmbeddingsProvider
from ..providers import BaseProvider, TextField


class OllamaProvider(BaseProvider, ChatOllama):
    id = "ollama"
    name = "Ollama"
    model_id_key = "model"
    help = (
        "See [https://www.ollama.com/library](https://www.ollama.com/library) for a list of models. "
        "Pass a model's name; for example, `deepseek-coder-v2`."
    )
    models = ["*"]
    registry = True
    fields = [
        TextField(key="base_url", label="Base API URL (optional)", format="text"),
    ]


class OllamaEmbeddingsProvider(BaseEmbeddingsProvider, OllamaEmbeddings):
    id = "ollama"
    name = "Ollama"
    # source: https://ollama.com/library
    model_id_key = "model"
    help = (
        "See [https://ollama.com/search?c=embedding](https://ollama.com/search?c=embedding) for a list of models. "
        "Pass an embedding model's name; for example, `mxbai-embed-large`."
    )
    models = ["*"]
    registry = True
    fields = [
        TextField(key="base_url", label="Base API URL (optional)", format="text"),
    ]
