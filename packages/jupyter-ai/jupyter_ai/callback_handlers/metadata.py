import json

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


def convert_to_serializable(obj):
    """Convert an object to a JSON serializable format"""
    if hasattr(obj, "dict") and callable(obj.dict):
        return obj.dict()
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
        serializable_metadata = {}
        for key, value in metadata.items():
            try:
                json.dumps(value)
                serializable_metadata[key] = value
            except (TypeError, ValueError):
                serializable_metadata[key] = convert_to_serializable(value)

        self.jai_metadata = serializable_metadata
