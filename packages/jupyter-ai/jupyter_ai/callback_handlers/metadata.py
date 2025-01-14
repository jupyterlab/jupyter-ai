import inspect
import json

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


def requires_no_arguments(func):
    sig = inspect.signature(func)
    for param in sig.parameters.values():
        if param.default is param.empty and param.kind in (
            param.POSITIONAL_ONLY,
            param.POSITIONAL_OR_KEYWORD,
            param.KEYWORD_ONLY,
        ):
            return False
    return True


def convert_to_serializable(obj):
    """Convert an object to a JSON serializable format"""
    if hasattr(obj, "dict") and callable(obj.dict) and requires_no_arguments(obj.dict):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


class MetadataCallbackHandler(BaseCallbackHandler):
    """
    When passed as a callback handler, this stores the LLMResult's
    `generation_info` dictionary in the `self.jai_metadata` instance attribute
    after the provider fully processes an input.

    If used in a streaming chat handler: the `metadata` field of the final
    `AgentStreamChunkMessage` should be set to `self.jai_metadata`.

    If used in a non-streaming chat handler: the `metadata` field of the
    returned `AgentChatMessage` should be set to `self.jai_metadata`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.jai_metadata = {}

    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        if not (len(response.generations) and len(response.generations[0])):
            return

        metadata = response.generations[0][0].generation_info or {}

        # Convert any non-serializable objects in metadata
        self.jai_metadata = json.loads(
            json.dumps(metadata, default=convert_to_serializable)
        )
