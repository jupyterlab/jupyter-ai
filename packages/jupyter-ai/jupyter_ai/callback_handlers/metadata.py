from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


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

        self.jai_metadata = response.generations[0][0].generation_info or {}
