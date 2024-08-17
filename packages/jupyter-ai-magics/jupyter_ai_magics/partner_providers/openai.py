from langchain_openai import (
    AzureChatOpenAI,
    AzureOpenAIEmbeddings,
    ChatOpenAI,
    OpenAI,
    OpenAIEmbeddings,
)

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


# https://platform.openai.com/docs/models/
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
        "gpt-4-turbo",
        "gpt-4-turbo-preview",
        "gpt-4-0613",
        "gpt-4-32k",
        "gpt-4-32k-0613",
        "gpt-4-0125-preview",
        "gpt-4-1106-preview",
        "gpt-4o",
        "gpt-4o-mini",
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
    model_id_key = "azure_deployment"
    model_id_label = "Deployment name"
    pypi_package_deps = ["langchain_openai"]
    # Confusingly, langchain uses both OPENAI_API_KEY and AZURE_OPENAI_API_KEY for azure
    # https://github.com/langchain-ai/langchain/blob/f2579096993ae460516a0aae1d3e09f3eb5c1772/libs/partners/openai/langchain_openai/llms/azure.py#L85
    auth_strategy = EnvAuthStrategy(
        name="AZURE_OPENAI_API_KEY", keyword_param="openai_api_key"
    )
    registry = True

    fields = [
        TextField(key="azure_endpoint", label="Base API URL (required)", format="text"),
        TextField(key="api_version", label="API version (required)", format="text"),
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


class AzureOpenAIEmbeddingsProvider(BaseEmbeddingsProvider, AzureOpenAIEmbeddings):
    id = "azure"
    name = "Azure OpenAI"
    models = [
        "text-embedding-ada-002",
        "text-embedding-3-small",
        "text-embedding-3-large",
    ]
    model_id_key = "azure_deployment"
    pypi_package_deps = ["langchain_openai"]
    auth_strategy = EnvAuthStrategy(
        name="AZURE_OPENAI_API_KEY", keyword_param="openai_api_key"
    )

    registry = True
