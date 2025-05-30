from jupyter_ai_magics import BaseProvider
from jupyter_ai_magics.base_provider import EnvAuthStrategy, TextField
from langchain_core.utils import get_from_dict_or_env
from langchain_openai import ChatOpenAI


class ChatOpenRouter(ChatOpenAI):
    @property
    def lc_secrets(self) -> dict[str, str]:
        return {"openai_api_key": "OPENROUTER_API_KEY"}


class OpenRouterProvider(BaseProvider, ChatOpenRouter):
    id = "openrouter"
    name = "OpenRouter"
    models = [
        "*"
    ]  # OpenRouter supports multiple models, so we use "*" to indicate it's a registry
    model_id_key = "model_name"
    pypi_package_deps = ["langchain_openai"]
    auth_strategy = EnvAuthStrategy(name="OPENROUTER_API_KEY")
    registry = True

    fields = [
        TextField(
            key="openai_api_base", label="API Base URL (optional)", format="text"
        ),
    ]

    def __init__(self, **kwargs):
        openrouter_api_key = get_from_dict_or_env(
            kwargs, key="openrouter_api_key", env_key="OPENROUTER_API_KEY", default=None
        )
        openrouter_api_base = kwargs.pop(
            "openai_api_base", "https://openrouter.ai/api/v1"
        )
        kwargs.pop("openrouter_api_key", None)
        super().__init__(
            openai_api_key=openrouter_api_key,
            openai_api_base=openrouter_api_base,
            **kwargs,
        )

    @classmethod
    def is_api_key_exc(cls, e: Exception):
        import openai

        if isinstance(e, openai.AuthenticationError):
            error_details = e.json_body.get("error", {})
            return error_details.get("code") == "invalid_api_key"
        return False
