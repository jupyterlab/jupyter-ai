from jupyter_ai_magics.providers import BaseProvider, EnvAuthStrategy
from langchain_mistralai import ChatMistralAI


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
        "mistral-embed",
        "codestral-latest",
    ]
    model_id_key = "model"
    auth_strategy = EnvAuthStrategy(name="MISTRAL_API_KEY")
    pypi_package_deps = ["langchain-mistralai"]
