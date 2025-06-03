from langchain_anthropic import ChatAnthropic

from ..base_provider import BaseProvider, EnvAuthStrategy


class ChatAnthropicProvider(
    BaseProvider, ChatAnthropic
):  # https://docs.anthropic.com/en/docs/about-claude/models
    id = "anthropic-chat"
    name = "Anthropic"
    models = [
        "claude-2.0",
        "claude-2.1",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-haiku-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-sonnet-20241022",
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
