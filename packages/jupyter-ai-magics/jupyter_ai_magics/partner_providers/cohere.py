from langchain_cohere import ChatCohere, CohereEmbeddings

from ..base_provider import BaseProvider, EnvAuthStrategy
from ..embedding_providers import BaseEmbeddingsProvider


class CohereProvider(BaseProvider, ChatCohere):
    id = "cohere"
    name = "Cohere"
    # https://docs.cohere.com/docs/models
    # note: This provider uses the Chat endpoint instead of the Generate
    # endpoint, which is now deprecated.
    models = [
        "command",
        "command-nightly",
        "command-light",
        "command-light-nightly",
        "command-r-plus",
        "command-r",
    ]
    model_id_key = "model"
    pypi_package_deps = ["langchain_cohere"]
    auth_strategy = EnvAuthStrategy(name="COHERE_API_KEY")


class CohereEmbeddingsProvider(BaseEmbeddingsProvider, CohereEmbeddings):
    id = "cohere"
    name = "Cohere"
    models = [
        "embed-english-v2.0",
        "embed-english-light-v2.0",
        "embed-multilingual-v2.0",
        "embed-english-v3.0",
        "embed-english-light-v3.0",
        "embed-multilingual-v3.0",
        "embed-multilingual-light-v3.0",
    ]
    model_id_key = "model"
    pypi_package_deps = ["langchain_cohere"]
    auth_strategy = EnvAuthStrategy(name="COHERE_API_KEY")
