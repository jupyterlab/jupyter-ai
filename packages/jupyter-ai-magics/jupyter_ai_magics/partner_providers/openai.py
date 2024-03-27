from langchain_openai import AzureChatOpenAI, ChatOpenAI, OpenAI, OpenAIEmbeddings

from ..embedding_providers import BaseEmbeddingsProvider
from ..providers import BaseProvider, EnvAuthStrategy, TextField


class OpenAIProvider(BaseProvider, OpenAI):
    id = "openai"
    name = "OpenAI"
    models = ["babbage-002", "davinci-002", "gpt-3.5-turbo-instruct"]
    model_id_key = "model_name"
    pypi_package_deps = ["langchain_openai"]
    auth_strategy = EnvAuthStrategy(name="OPENAI_API_KEY")

    @classmethod
    def is_api_key_exc(cls, e: Exception):
        """
        Determine if the exception is an OpenAI API key error.
        """
        import openai

        if isinstance(e, openai.AuthenticationError):
            error_details = e.json_body.get("error", {})
            return error_details.get("code") == "invalid_api_key"
        return False


class ChatOpenAIProvider(BaseProvider, ChatOpenAI):
    id = "openai-chat"
    name = "OpenAI"
    models = [
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0125",
        "gpt-3.5-turbo-0301",  # Deprecated as of 2024-06-13
        "gpt-3.5-turbo-0613",  # Deprecated as of 2024-06-13
        "gpt-3.5-turbo-1106",
        "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-16k-0613",  # Deprecated as of 2024-06-13
        "gpt-4",
        "gpt-4-turbo-preview",
        "gpt-4-0613",
        "gpt-4-32k",
        "gpt-4-32k-0613",
        "gpt-4-0125-preview",
        "gpt-4-1106-preview",
    ]
    model_id_key = "model_name"
    pypi_package_deps = ["langchain_openai"]
    auth_strategy = EnvAuthStrategy(name="OPENAI_API_KEY")

    fields = [
        TextField(
            key="openai_api_base", label="Base API URL (optional)", format="text"
        ),
        TextField(
            key="openai_organization", label="Organization (optional)", format="text"
        ),
        TextField(key="openai_proxy", label="Proxy (optional)", format="text"),
    ]

    @classmethod
    def is_api_key_exc(cls, e: Exception):
        """
        Determine if the exception is an OpenAI API key error.
        """
        import openai

        if isinstance(e, openai.AuthenticationError):
            error_details = e.json_body.get("error", {})
            return error_details.get("code") == "invalid_api_key"
        return False


class AzureChatOpenAIProvider(BaseProvider, AzureChatOpenAI):
    id = "azure-chat-openai"
    name = "Azure OpenAI"
    models = ["*"]
    model_id_key = "deployment_name"
    model_id_label = "Deployment name"
    pypi_package_deps = ["langchain_openai"]
    auth_strategy = EnvAuthStrategy(name="AZURE_OPENAI_API_KEY")
    registry = True

    fields = [
        TextField(
            key="openai_api_base", label="Base API URL (required)", format="text"
        ),
        TextField(
            key="openai_api_version", label="API version (required)", format="text"
        ),
        TextField(
            key="openai_organization", label="Organization (optional)", format="text"
        ),
        TextField(key="openai_proxy", label="Proxy (optional)", format="text"),
    ]


class OpenAIEmbeddingsProvider(BaseEmbeddingsProvider, OpenAIEmbeddings):
    id = "openai"
    name = "OpenAI"
    models = [
        "text-embedding-ada-002",
        "text-embedding-3-small",
        "text-embedding-3-large",
    ]
    model_id_key = "model"
    pypi_package_deps = ["langchain_openai"]
    auth_strategy = EnvAuthStrategy(name="OPENAI_API_KEY")
