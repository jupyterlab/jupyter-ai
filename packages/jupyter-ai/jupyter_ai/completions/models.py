from typing import List, Literal, Optional

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
    # suffix should include full text of the current cell preceding the cursor
    suffix: str
    # media type for the current language, e.g. `text/x-python`
    mime: str
    # path to the notebook of file for which the completions are generated
    path: Optional[str]
    # language inferred from the document mime type (if possible)
    language: Optional[str]
    # identifier of the cell for which the completions are generated if in a notebook
    # previous cells and following cells can be used to learn the wider context
    cell_id: Optional[str]


class InlineCompletionItem(BaseModel):
    """The inline completion suggestion to be displayed on the frontend.

    See JuptyerLab `InlineCompletionItem` documentation for the details.
    """

    insertText: str
    filterText: Optional[str]
    isIncomplete: Optional[bool]
    token: Optional[bool]


class CompletionError(BaseModel):
    type: str
    traceback: str


class InlineCompletionList(BaseModel):
    """Reflection of JupyterLab's `IInlineCompletionList`."""

    items: List[InlineCompletionItem]


class InlineCompletionReply(BaseModel):
    """Message sent from model to client with the infill suggestions"""

    list: InlineCompletionList
    # number of request for which we are replying
    reply_to: int
    error: Optional[CompletionError]


class ModelChangedNotification(BaseModel):
    type: Literal["model_changed"] = "model_changed"
    model: Optional[str]
