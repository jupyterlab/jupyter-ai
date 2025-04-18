from typing import Literal, Optional

from pydantic import BaseModel


class InlineCompletionRequest(BaseModel):
    """Message send by client to request inline completions.

    Prefix/suffix implementation is used to avoid the need for synchronising
    the notebook state at every key press (subject to change in future)."""

    # unique message ID generated by the client used to identify replies and
    # to easily discard replies for older requests
    number: int
    # prefix should include full text of the current cell preceding the cursor
    prefix: str
    # suffix should include full text of the current cell following the cursor
    suffix: str
    # media type for the current language, e.g. `text/x-python`
    mime: str
    # whether to stream the response (if supported by the model)
    stream: bool
    # path to the notebook of file for which the completions are generated
    path: Optional[str] = None
    # language inferred from the document mime type (if possible)
    language: Optional[str] = None
    # identifier of the cell for which the completions are generated if in a notebook
    # previous cells and following cells can be used to learn the wider context
    cell_id: Optional[str] = None


class InlineCompletionItem(BaseModel):
    """The inline completion suggestion to be displayed on the frontend.

    See JupyterLab `InlineCompletionItem` documentation for the details.
    """

    insertText: str
    filterText: Optional[str] = None
    isIncomplete: Optional[bool] = None
    token: Optional[str] = None


class CompletionError(BaseModel):
    type: str
    title: str
    traceback: str


class InlineCompletionList(BaseModel):
    """Reflection of JupyterLab's `IInlineCompletionList`."""

    items: list[InlineCompletionItem]


class InlineCompletionReply(BaseModel):
    """Message sent from model to client with the infill suggestions"""

    list: InlineCompletionList
    # number of request for which we are replying
    reply_to: int
    error: Optional[CompletionError] = None


class InlineCompletionStreamChunk(BaseModel):
    """Message sent from model to client with the infill suggestions"""

    type: Literal["stream"] = "stream"
    response: InlineCompletionItem
    reply_to: int
    done: bool
    error: Optional[CompletionError] = None


__all__ = [
    "InlineCompletionRequest",
    "InlineCompletionItem",
    "CompletionError",
    "InlineCompletionList",
    "InlineCompletionReply",
    "InlineCompletionStreamChunk",
]
