from typing import Dict, Type

from jupyter_ai_magics.providers import BaseProvider
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import Runnable

from ..models import (
    InlineCompletionList,
    InlineCompletionReply,
    InlineCompletionRequest,
    InlineCompletionStreamChunk,
)
from .base import BaseInlineCompletionHandler


class DefaultInlineCompletionHandler(BaseInlineCompletionHandler):
    llm_chain: Runnable

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        unified_parameters = {
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        llm = provider(**unified_parameters)

        prompt_template = llm.get_completion_prompt_template()

        self.llm = llm
        self.llm_chain = prompt_template | llm | StrOutputParser()

    async def handle_request(self, request: InlineCompletionRequest) -> None:
        """Handles an inline completion request without streaming."""
        self.get_llm_chain()
        model_arguments = await self._template_inputs_from_request(request)
        suggestion = await self.llm_chain.ainvoke(input=model_arguments)
        suggestion = self._post_process_suggestion(suggestion, request)
        self.write_message(
            InlineCompletionReply(
                list=InlineCompletionList(items=[{"insertText": suggestion}]),
                reply_to=request.number,
            )
        )

    def _write_incomplete_reply(self, request: InlineCompletionRequest):
        """Writes an incomplete `InlineCompletionReply`, indicating to the
        client that LLM output is about to streamed across this connection.
        Should be called first in `self.handle_stream_request()`."""

        token = self._token_from_request(request, 0)
        reply = InlineCompletionReply(
            list=InlineCompletionList(
                items=[
                    {
                        # insert text starts empty as we do not pre-generate any part
                        "insertText": "",
                        "isIncomplete": True,
                        "token": token,
                    }
                ]
            ),
            reply_to=request.number,
        )
        self.write_message(reply)

    async def handle_stream_request(self, request: InlineCompletionRequest):
        # first, send empty initial reply.
        self._write_incomplete_reply(request)

        # then, generate and stream LLM output over this connection.
        self.get_llm_chain()
        token = self._token_from_request(request, 0)
        model_arguments = await self._template_inputs_from_request(request)
        suggestion = ""

        async for fragment in self.llm_chain.astream(input=model_arguments):
            suggestion += fragment
            if suggestion.startswith("```"):
                if "\n" not in suggestion:
                    # we are not ready to apply post-processing
                    continue
                else:
                    suggestion = self._post_process_suggestion(suggestion, request)
            self.write_message(
                InlineCompletionStreamChunk(
                    type="stream",
                    response={"insertText": suggestion, "token": token},
                    reply_to=request.number,
                    done=False,
                )
            )

        # finally, send a message confirming that we are done
        self.write_message(
            InlineCompletionStreamChunk(
                type="stream",
                response={"insertText": suggestion, "token": token},
                reply_to=request.number,
                done=True,
            )
        )

    def _token_from_request(self, request: InlineCompletionRequest, suggestion: int):
        """Generate a deterministic token (for matching streamed messages)
        using request number and suggestion number"""
        return f"t{request.number}s{suggestion}"

    async def _get_document(self, request: InlineCompletionRequest):
        collaboration = self.settings.get("jupyter_collaboration", None)
        file_id_manager = self.settings.get("file_id_manager", None)

        if not collaboration or not file_id_manager or not request.path:
            return None

        from jupyter_collaboration.rooms import DocumentRoom
        from jupyter_collaboration.utils import encode_file_path
        from jupyter_collaboration.websocketserver import RoomNotFound

        file_id = file_id_manager.index(request.path)
        is_notebook = request.path.endswith("ipynb")
        content_type = "notebook" if is_notebook else "file"
        file_format = "json" if is_notebook else "text"

        encoded_path = encode_file_path(file_format, content_type, file_id)
        room_id: str = encoded_path.split("/")[-1]

        try:
            room = await collaboration.ywebsocket_server.get_room(room_id)
        except RoomNotFound:
            return None

        if isinstance(room, DocumentRoom):
            document = room._document
            return document

    async def _template_inputs_from_request(
        self, request: InlineCompletionRequest
    ) -> Dict:
        prefix = request.prefix
        suffix = request.suffix.strip()
        filename = request.path.split("/")[-1] if request.path else "untitled"

        document = await self._get_document(request)

        if document:
            from jupyter_ydoc import YNotebook

        if document and isinstance(document, YNotebook):
            cell_type = "markdown" if request.language == "markdown" else "code"

            is_before_request_cell = True
            before = []
            after = [suffix]

            for cell in document.ycells:
                if is_before_request_cell and cell["id"] == request.cell_id:
                    is_before_request_cell = False
                    continue
                if cell["cell_type"] != cell_type:
                    continue
                source = cell["source"].to_py()
                if is_before_request_cell:
                    before.append(source)
                else:
                    after.append(source)

            before.append(prefix)
            prefix = "\n\n".join(before)
            suffix = "\n\n".join(after)

        return {
            "prefix": prefix,
            "suffix": suffix,
            "language": request.language,
            "filename": filename,
            "stop": ["\n```"],
        }

    def _post_process_suggestion(
        self, suggestion: str, request: InlineCompletionRequest
    ) -> str:
        """Remove spurious fragments from the suggestion.

        While most models (especially instruct and infill models do not require
        any pre-processing, some models such as gpt-4 which only have chat APIs
        may require removing spurious fragments. This function uses heuristics
        and request data to remove such fragments.
        """
        # gpt-4 tends to add "```python" or similar
        language = request.language or "python"
        markdown_identifiers = {"ipython": ["ipython", "python", "py"]}
        bad_openings = [
            f"```{identifier}"
            for identifier in markdown_identifiers.get(language, [language])
        ] + ["```"]
        for opening in bad_openings:
            if suggestion.startswith(opening):
                suggestion = suggestion[len(opening) :].lstrip()
                # check for the prefix inclusion (only if there was a bad opening)
                if suggestion.startswith(request.prefix):
                    suggestion = suggestion[len(request.prefix) :]
                break
        return suggestion
