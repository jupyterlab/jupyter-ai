import copy
import json
from typing import Any, Coroutine, Dict

from jsonpath_ng import parse
from langchain_aws import BedrockEmbeddings, BedrockLLM, ChatBedrock, SagemakerEndpoint
from langchain_aws.llms.sagemaker_endpoint import LLMContentHandler
from langchain_core.outputs import LLMResult

from ..embedding_providers import BaseEmbeddingsProvider
from ..providers import AwsAuthStrategy, BaseProvider, MultilineTextField, TextField


# See model ID list here: https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
class BedrockProvider(BaseProvider, BedrockLLM):
    id = "bedrock"
    name = "Amazon Bedrock"
    models = [
        "amazon.titan-text-express-v1",
        "amazon.titan-text-lite-v1",
        "amazon.titan-text-premier-v1:0",
        "ai21.j2-ultra-v1",
        "ai21.j2-mid-v1",
        "ai21.jamba-instruct-v1:0",
        "cohere.command-light-text-v14",
        "cohere.command-text-v14",
        "cohere.command-r-v1:0",
        "cohere.command-r-plus-v1:0",
        "mistral.mistral-7b-instruct-v0:2",
        "mistral.mixtral-8x7b-instruct-v0:1",
        "mistral.mistral-large-2402-v1:0",
        "mistral.mistral-large-2407-v1:0",
    ]
    model_id_key = "model_id"
    pypi_package_deps = ["langchain-aws"]
    auth_strategy = AwsAuthStrategy()
    fields = [
        TextField(
            key="credentials_profile_name",
            label="AWS profile (optional)",
            format="text",
        ),
        TextField(key="region_name", label="Region name (optional)", format="text"),
    ]

    async def _acall(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        return await self._call_in_executor(*args, **kwargs)


# See model ID list here: https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
class BedrockChatProvider(BaseProvider, ChatBedrock):
    id = "bedrock-chat"
    name = "Amazon Bedrock Chat"

    cri_models = [
        # Anthropic models
        "anthropic.claude-3-haiku-20240307-v1:0",
        "anthropic.claude-3-5-haiku-20241022-v1:0",
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "anthropic.claude-3-opus-20240229-v1:0",
        # Meta Llama 3.1 models
        "meta.llama3-1-8b-instruct-v1:0",
        "meta.llama3-1-70b-instruct-v1:0",
        # Meta Llama 3.2 models
        "meta.llama3-2-1b-instruct-v1:0",
        "meta.llama3-2-3b-instruct-v1:0",
        "meta.llama3-2-11b-instruct-v1:0",
        "meta.llama3-2-90b-instruct-v1:0",
    ]
    """
    List of model IDs that support cross-region inference (CRI) in the "us" region area.

    - If a model supports CRI, we default to invoking CRI as it allows the model to be called regardless of the user's region.
    - To invoke CRI, we prepend "us." to the model ID internally, which transforms it into an inference profile ID, indicating that CRI should be used.
    - Currently, we only support CRI to the "us" region area.

    Source: https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html
    """

    models = [
        *cri_models,
        # Amazon models (no CRI)
        "amazon.titan-text-express-v1",
        "amazon.titan-text-lite-v1",
        "amazon.titan-text-premier-v1:0",
        # Anthropic v1 & v2 models (no CRI)
        "anthropic.claude-v2",
        "anthropic.claude-v2:1",
        "anthropic.claude-instant-v1",
        # Meta Llama 2 models (no CRI)
        "meta.llama2-13b-chat-v1",
        "meta.llama2-70b-chat-v1",
        # Meta Llama 3 models (no CRI)
        "meta.llama3-8b-instruct-v1:0",
        "meta.llama3-70b-instruct-v1:0",
        # Meta Llama 3.1 models (only one not supporting CRI)
        "meta.llama3-1-405b-instruct-v1:0",
        # Mistral models
        "mistral.mistral-7b-instruct-v0:2",
        "mistral.mixtral-8x7b-instruct-v0:1",
        "mistral.mistral-large-2402-v1:0",
        "mistral.mistral-large-2407-v1:0",
    ]
    model_id_key = "model_id"
    pypi_package_deps = ["langchain-aws"]
    auth_strategy = AwsAuthStrategy()
    fields = [
        TextField(
            key="credentials_profile_name",
            label="AWS profile (optional)",
            format="text",
        ),
        TextField(key="region_name", label="Region name (optional)", format="text"),
    ]

    def __init__(self, *args, **kwargs):
        model_id = kwargs.pop("model_id")
        if model_id in self.cri_models:
            model_id = "us." + model_id

        super().__init__(*args, **kwargs, model_id=model_id)

    async def _acall(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        return await self._call_in_executor(*args, **kwargs)

    async def _agenerate(self, *args, **kwargs) -> Coroutine[Any, Any, LLMResult]:
        return await self._generate_in_executor(*args, **kwargs)

    @property
    def allows_concurrency(self):
        return not "anthropic" in self.model_id


class BedrockCustomProvider(BaseProvider, ChatBedrock):
    id = "bedrock-custom"
    name = "Amazon Bedrock (custom/provisioned)"
    models = ["*"]
    model_id_key = "model_id"
    model_id_label = "Model ID"
    pypi_package_deps = ["langchain-aws"]
    auth_strategy = AwsAuthStrategy()
    fields = [
        TextField(key="provider", label="Provider (required)", format="text"),
        TextField(key="region_name", label="Region name (optional)", format="text"),
        TextField(
            key="credentials_profile_name",
            label="AWS profile (optional)",
            format="text",
        ),
    ]
    help = (
        "Specify the ARN (Amazon Resource Name) of the custom/provisioned model as the model ID. For more information, see the [Amazon Bedrock model IDs documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html).\n\n"
        "The model provider must also be specified below. This is the provider of your foundation model *in lowercase*, e.g. `amazon`, `anthropic`, `meta`, or `mistral`."
    )
    registry = True


# See model ID list here: https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
class BedrockEmbeddingsProvider(BaseEmbeddingsProvider, BedrockEmbeddings):
    id = "bedrock"
    name = "Bedrock"
    models = [
        "amazon.titan-embed-text-v1",
        "amazon.titan-embed-text-v2:0",
        "cohere.embed-english-v3",
        "cohere.embed-multilingual-v3",
    ]
    model_id_key = "model_id"
    pypi_package_deps = ["langchain-aws"]
    auth_strategy = AwsAuthStrategy()


class JsonContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def __init__(self, request_schema, response_path):
        self.request_schema = json.loads(request_schema)
        self.response_path = response_path
        self.response_parser = parse(response_path)

    def replace_values(self, old_val, new_val, d: Dict[str, Any]):
        """Replaces values of a dictionary recursively."""
        for key, val in d.items():
            if val == old_val:
                d[key] = new_val
            if isinstance(val, dict):
                self.replace_values(old_val, new_val, val)

        return d

    def transform_input(self, prompt: str, model_kwargs: Dict) -> bytes:
        request_obj = copy.deepcopy(self.request_schema)
        self.replace_values("<prompt>", prompt, request_obj)
        request = json.dumps(request_obj).encode("utf-8")
        return request

    def transform_output(self, output: bytes) -> str:
        response_json = json.loads(output.read().decode("utf-8"))
        matches = self.response_parser.find(response_json)
        return matches[0].value


class SmEndpointProvider(BaseProvider, SagemakerEndpoint):
    id = "sagemaker-endpoint"
    name = "SageMaker endpoint"
    models = ["*"]
    model_id_key = "endpoint_name"
    model_id_label = "Endpoint name"
    # This all needs to be on one line of markdown, for use in a table
    help = (
        "Specify an endpoint name as the model ID. "
        "In addition, you must specify a region name, request schema, and response path. "
        "For more information, see the documentation about [SageMaker endpoints deployment](https://docs.aws.amazon.com/sagemaker/latest/dg/realtime-endpoints-deploy-models.html) "
        "and about [using magic commands with SageMaker endpoints](https://jupyter-ai.readthedocs.io/en/latest/users/index.html#using-magic-commands-with-sagemaker-endpoints)."
    )

    pypi_package_deps = ["langchain-aws"]
    auth_strategy = AwsAuthStrategy()
    registry = True
    fields = [
        TextField(key="region_name", label="Region name (required)", format="text"),
        MultilineTextField(
            key="request_schema", label="Request schema (required)", format="json"
        ),
        TextField(
            key="response_path", label="Response path (required)", format="jsonpath"
        ),
    ]

    def __init__(self, *args, **kwargs):
        request_schema = kwargs.pop("request_schema")
        response_path = kwargs.pop("response_path")
        content_handler = JsonContentHandler(
            request_schema=request_schema, response_path=response_path
        )

        super().__init__(*args, **kwargs, content_handler=content_handler)

    async def _acall(self, *args, **kwargs) -> Coroutine[Any, Any, str]:
        return await self._call_in_executor(*args, **kwargs)
