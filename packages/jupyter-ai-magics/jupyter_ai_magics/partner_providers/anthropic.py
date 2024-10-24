from langchain_anthropic import AnthropicLLM, ChatAnthropic

from ..providers import BaseProvider, EnvAuthStrategy


class AnthropicProvider(BaseProvider, AnthropicLLM):
    id = "anthropic"
    name = "Anthropic"
    models = [
        "claude-v1",
        "claude-v1.0",
        "claude-v1.2",
        "claude-2",
        "claude-2.0",
        "claude-instant-v1",
        "claude-instant-v1.0",
        "claude-instant-v1.2",
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


class ChatAnthropicProvider(
    BaseProvider, ChatAnthropic
):  # https://docs.anthropic.com/en/docs/about-claude/models
    id = "anthropic-chat"
    name = "ChatAnthropic"
    models = [
        "claude-2.0",
        "claude-2.1",
        "claude-instant-1.2",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20240620",
    ]
    model_id_key = "model"
    pypi_package_deps = ["anthropic"]
    auth_strategy = EnvAuthStrategy(name="ANTHROPIC_API_KEY")

    @property
    def allows_concurrency(self):
        return False
