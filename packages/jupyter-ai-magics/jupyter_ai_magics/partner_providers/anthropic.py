from langchain_anthropic import ChatAnthropic

from ..base_provider import BaseProvider, EnvAuthStrategy


class ChatAnthropicProvider(
    BaseProvider, ChatAnthropic
):  # https://docs.anthropic.com/en/docs/about-claude/models
    id = "anthropic-chat"
    name = "Anthropic"
    models = [
        # Claude 4.5 models (current flagship)
        "claude-sonnet-4-5-20250929",
        "claude-opus-4-5-20251101",
        "claude-haiku-4-5-20251001",
        # Claude 4 models (2025 releases)
        "claude-opus-4-1-20250805",
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514",
        # Claude 3.7 models
        "claude-3-7-sonnet-20250219",
        # Claude 3.5 models (still supported)
        "claude-3-5-haiku-20241022",
        "claude-3-5-sonnet-20241022",
        # Claude 3 models (legacy but still supported)
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]
    model_id_key = "model"
    pypi_package_deps = ["anthropic"]
    auth_strategy = EnvAuthStrategy(name="ANTHROPIC_API_KEY")

    @property
    def allows_concurrency(self):
        return False

    @classmethod
    def is_api_key_exc(cls, e: Exception):
        """
        Determine if the exception is an Anthropic API key error.
        """
        import anthropic

        if isinstance(e, anthropic.AuthenticationError):
            return e.status_code == 401 and "Invalid API Key" in str(e)
        return False
