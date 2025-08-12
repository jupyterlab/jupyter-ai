from ..completion_types import InlineCompletionRequest
from .base import BaseInlineCompletionHandler


class DefaultInlineCompletionHandler(BaseInlineCompletionHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def handle_request(self, request: InlineCompletionRequest):
        """Handles an inline completion request without streaming."""
        # TODO: migrate this to use LiteLLM
        # llm = self.get_llm()
        # if not llm:
        #     raise ValueError("Please select a model for inline completion.")

        # reply = await llm.generate_inline_completions(request)
        # self.reply(reply)

    async def handle_stream_request(self, request: InlineCompletionRequest):
        # TODO: migrate this to use LiteLLM
        # llm = self.get_llm()
        # if not llm:
        #     raise ValueError("Please select a model for inline completion.")

        # async for reply in llm.stream_inline_completions(request):
        #     self.reply(reply)
        pass


# old methods on BaseProvider, for reference when migrating this to LiteLLM
#
# async def generate_inline_completions(
#     self, request: InlineCompletionRequest
# ) -> InlineCompletionReply:
#     chain = self._create_completion_chain()
#     model_arguments = completion.template_inputs_from_request(request)
#     suggestion = await chain.ainvoke(input=model_arguments)
#     suggestion = completion.post_process_suggestion(suggestion, request)
#     return InlineCompletionReply(
#         list=InlineCompletionList(items=[{"insertText": suggestion}]),
#         reply_to=request.number,
#     )

# async def stream_inline_completions(
#     self, request: InlineCompletionRequest
# ) -> AsyncIterator[InlineCompletionStreamChunk]:
#     chain = self._create_completion_chain()
#     token = completion.token_from_request(request, 0)
#     model_arguments = completion.template_inputs_from_request(request)
#     suggestion = processed_suggestion = ""

#     # send an incomplete `InlineCompletionReply`, indicating to the
#     # client that LLM output is about to streamed across this connection.
#     yield InlineCompletionReply(
#         list=InlineCompletionList(
#             items=[
#                 {
#                     # insert text starts empty as we do not pre-generate any part
#                     "insertText": "",
#                     "isIncomplete": True,
#                     "token": token,
#                 }
#             ]
#         ),
#         reply_to=request.number,
#     )

#     async for fragment in chain.astream(input=model_arguments):
#         suggestion += fragment
#         processed_suggestion = completion.post_process_suggestion(
#             suggestion, request
#         )
#         yield InlineCompletionStreamChunk(
#             type="stream",
#             response={"insertText": processed_suggestion, "token": token},
#             reply_to=request.number,
#             done=False,
#         )

#     # finally, send a message confirming that we are done
#     yield InlineCompletionStreamChunk(
#         type="stream",
#         response={"insertText": processed_suggestion, "token": token},
#         reply_to=request.number,
#         done=True,
#     )
