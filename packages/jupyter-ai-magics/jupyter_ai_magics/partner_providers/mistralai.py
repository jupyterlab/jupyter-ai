from jupyter_ai_magics.base_provider import BaseProvider, EnvAuthStrategy
from langchain_mistralai import ChatMistralAI, MistralAIEmbeddings

from ..embedding_providers import BaseEmbeddingsProvider


class MistralAIProvider(BaseProvider, ChatMistralAI):
    id = "mistralai"
    name = "MistralAI"
    models = [
        "open-mistral-7b",
        "open-mixtral-8x7b",
        "open-mixtral-8x22b",
        "mistral-small-latest",
        "mistral-medium-latest",
        "mistral-large-latest",
        "codestral-latest",
    ]
    model_id_key = "model"
    auth_strategy = EnvAuthStrategy(name="MISTRAL_API_KEY")
    pypi_package_deps = ["langchain-mistralai"]


class MistralAIEmbeddingsProvider(BaseEmbeddingsProvider, MistralAIEmbeddings):
    id = "mistralai"
    name = "MistralAI"
    models = [
        "mistral-embed",
    ]
    model_id_key = "model"
    pypi_package_deps = ["langchain-mistralai"]
    auth_strategy = EnvAuthStrategy(name="MISTRAL_API_KEY")
