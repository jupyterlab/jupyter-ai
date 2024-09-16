from typing import Dict

from jupyter_ai_magics import BaseProvider
from jupyter_ai_magics.providers import EnvAuthStrategy, TextField
from langchain_core.pydantic_v1 import root_validator
from langchain_core.utils import convert_to_secret_str, get_from_dict_or_env
from langchain_openai import ChatOpenAI


class ChatOpenRouter(ChatOpenAI):
    @property
    def lc_secrets(self) -> Dict[str, str]:
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
        openrouter_api_key = kwargs.pop("openrouter_api_key", None)
        openrouter_api_base = kwargs.pop(
            "openai_api_base", "https://openrouter.ai/api/v1"
        )

        super().__init__(
            openai_api_key=openrouter_api_key,
            openai_api_base=openrouter_api_base,
            **kwargs,
        )

    @root_validator(pre=False, skip_on_failure=True, allow_reuse=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        values["openai_api_key"] = convert_to_secret_str(
            get_from_dict_or_env(values, "openai_api_key", "OPENROUTER_API_KEY")
        )
        return super().validate_environment(values)

    @classmethod
    def is_api_key_exc(cls, e: Exception):
        import openai

        if isinstance(e, openai.AuthenticationError):
            error_details = e.json_body.get("error", {})
            return error_details.get("code") == "invalid_api_key"
        return False
