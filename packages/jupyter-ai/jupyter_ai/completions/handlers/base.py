import time
import traceback

# necessary to prevent circular import
from typing import TYPE_CHECKING, Dict
from uuid import uuid4

from jupyter_ai.completions.models import (
    CompletionError,
    InlineCompletionReply,
    InlineCompletionRequest,
    ModelChangedNotification,
)
from jupyter_ai.config_manager import ConfigManager, Logger
from jupyter_ai.llm_handler import BaseLLMHandler

if TYPE_CHECKING:
    from jupyter_ai.handlers import InlineCompletionHandler


class BaseInlineCompletionHandler(BaseLLMHandler):
    """Class implementing completion handling."""

    def __init__(
        self,
        log: Logger,
        config_manager: ConfigManager,
        model_parameters: Dict[str, Dict],
        ws_sessions: Dict[str, "InlineCompletionHandler"],
    ):
        super().__init__(log, config_manager, model_parameters)
        self.ws_sessions = ws_sessions

    async def on_message(
        self, message: InlineCompletionRequest
    ) -> InlineCompletionReply:
        try:
            return await self.process_message(message)
        except Exception as e:
            return await self._handle_exc(e, message)

    async def process_message(
        self, message: InlineCompletionRequest
    ) -> InlineCompletionReply:
        """
        Processes an inline completion request. Completion handlers
        (subclasses) must implement this method.

        The method definition does not need to be wrapped in a try/except block.
        """
        raise NotImplementedError("Should be implemented by subclasses.")

    async def _handle_exc(self, e: Exception, message: InlineCompletionRequest):
        error = CompletionError(
            type=e.__class__.__name__,
            title=e.args[0] if e.args else "Exception",
            traceback=traceback.format_exc(),
        )
        return InlineCompletionReply(items=[], error=error)

    def broadcast(self, message: ModelChangedNotification):
        for session in self.ws_sessions.values():
            session.write_message(message.dict())
