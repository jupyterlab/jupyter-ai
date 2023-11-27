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
    ModelChangedNotification,
)
from .base import BaseInlineCompletionHandler

SYSTEM_PROMPT = """
You are an application built to provide helpful code completion suggestions.
You should only produce code. Keep comments to minimum, use the
programming language comment syntax. Produce clean code.
The code is written in JupyterLab, a data analysis and code development
environment which can execute code extended with additional syntax for
interactive features, such as magics.
""".strip()

AFTER_TEMPLATE = """
The code after the completion request is:

```
{suffix}
```
""".strip()

DEFAULT_TEMPLATE = """
The document is called `{filename}` and written in {language}.
{after}

Complete the following code:

```
{prefix}"""


class DefaultInlineCompletionHandler(BaseInlineCompletionHandler):
    llm_chain: Runnable

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        lm_provider = self.config_manager.lm_provider
        lm_provider_params = self.config_manager.lm_provider_params
        next_lm_id = (
            f'{lm_provider.id}:{lm_provider_params["model_id"]}'
            if lm_provider
            else None
        )
        self.broadcast(ModelChangedNotification(model=next_lm_id))

        model_parameters = self.get_model_parameters(provider, provider_params)
        llm = provider(**provider_params, **model_parameters)

        if llm.is_chat_provider:
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
                    HumanMessagePromptTemplate.from_template(DEFAULT_TEMPLATE),
                ]
            )
        else:
            prompt_template = PromptTemplate(
                input_variables=["prefix", "suffix", "language", "filename"],
                template=SYSTEM_PROMPT + "\n\n" + DEFAULT_TEMPLATE,
            )

        self.llm = llm
        self.llm_chain = prompt_template | llm | StrOutputParser()

    async def process_message(
        self, request: InlineCompletionRequest
    ) -> InlineCompletionReply:
        if request.stream:
            token = self._token_from_request(request, 0)
            return InlineCompletionReply(
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
        else:
            self.get_llm_chain()
            model_arguments = self._template_inputs_from_request(request)
            suggestion = await self.llm_chain.ainvoke(input=model_arguments)
            suggestion = self._post_process_suggestion(suggestion, request)
            return InlineCompletionReply(
                list=InlineCompletionList(items=[{"insertText": suggestion}]),
                reply_to=request.number,
            )

    async def stream(self, request: InlineCompletionRequest):
        self.get_llm_chain()
        token = self._token_from_request(request, 0)
        model_arguments = self._template_inputs_from_request(request)
        suggestion = ""
        async for fragment in self.llm_chain.astream(input=model_arguments):
            suggestion += fragment
            if suggestion.startswith("```"):
                if "\n" not in suggestion:
                    # we are not ready to apply post-processing
                    continue
                else:
                    suggestion = self._post_process_suggestion(suggestion, request)
            yield InlineCompletionStreamChunk(
                type="stream",
                response={"insertText": suggestion, "token": token},
                reply_to=request.number,
                done=False,
            )
        # at the end send a message confirming that we are done
        yield InlineCompletionStreamChunk(
            type="stream",
            response={"insertText": suggestion, "token": token},
            reply_to=request.number,
            done=True,
        )

    def _token_from_request(self, request: InlineCompletionRequest, suggestion: int):
        """Generate a deterministic token (for matching streamed messages)
        using request number and suggestion number"""
        return f"t{request.number}s{suggestion}"

    def _template_inputs_from_request(self, request: InlineCompletionRequest) -> Dict:
        suffix = request.suffix.strip()
        # only add the suffix template if the suffix is there to save input tokens/computation time
        after = AFTER_TEMPLATE.format(suffix=suffix) if suffix else ""
        filename = request.path.split("/")[-1] if request.path else "untitled"

        return {
            "prefix": request.prefix,
            "after": after,
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
