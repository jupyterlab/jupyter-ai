from ..models import InlineCompletionRequest
from .base import BaseInlineCompletionHandler


class DefaultInlineCompletionHandler(BaseInlineCompletionHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def handle_request(self, request: InlineCompletionRequest):
        """Handles an inline completion request without streaming."""
        llm = self.get_llm()
        if not llm:
            raise ValueError("Please select a model for inline completion.")

        reply = await llm.generate_inline_completions(request)
        self.reply(reply)

    async def handle_stream_request(self, request: InlineCompletionRequest):
        llm = self.get_llm()
        if not llm:
            raise ValueError("Please select a model for inline completion.")

        async for reply in llm.stream_inline_completions(request):
            self.reply(reply)
