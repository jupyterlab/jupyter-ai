import json
import time
import traceback
from asyncio import AbstractEventLoop
from typing import Union

import tornado
from jupyter_ai.completions.handlers.model_mixin import CompletionsModelMixin
from jupyter_ai.completions.models import (
    CompletionError,
    InlineCompletionList,
    InlineCompletionReply,
    InlineCompletionRequest,
    InlineCompletionStreamChunk,
)
from jupyter_server.base.handlers import JupyterHandler
from langchain.pydantic_v1 import ValidationError


class BaseInlineCompletionHandler(
    CompletionsModelMixin, JupyterHandler, tornado.websocket.WebSocketHandler
):
    """A Tornado WebSocket handler that receives inline completion requests and
    fulfills them accordingly. This class is instantiated once per WebSocket
    connection."""

    ##
    # Interface for subclasses
    ##
    async def handle_request(self, message: InlineCompletionRequest) -> None:
        """
        Handles an inline completion request, without streaming. Subclasses
        must define this method and write a reply via `self.reply()`.

        The method definition does not need to be wrapped in a try/except block.
        """
        raise NotImplementedError(
            "The required method `self.handle_request()` is not defined by this subclass."
        )

    async def handle_stream_request(self, message: InlineCompletionRequest) -> None:
        """
        Handles an inline completion request, **with streaming**.
        Implementations may optionally define this method. Implementations that
        do so should stream replies via successive calls to `self.reply()`.

        The method definition does not need to be wrapped in a try/except block.
        """
        raise NotImplementedError(
            "The optional method `self.handle_stream_request()` is not defined by this subclass."
        )

    ##
    # Definition of base class
    ##
    handler_kind = "completion"

    @property
    def loop(self) -> AbstractEventLoop:
        return self.settings["jai_event_loop"]

    def reply(self, reply: Union[InlineCompletionReply, InlineCompletionStreamChunk]):
        """Write a reply object to the WebSocket connection."""
        message = reply.dict()
        super().write_message(message)

    def initialize(self):
        self.log.debug("Initializing websocket connection %s", self.request.path)

    def pre_get(self):
        """Handles authentication/authorization."""
        # authenticate the request before opening the websocket
        user = self.current_user
        if user is None:
            self.log.warning("Couldn't authenticate WebSocket connection")
            raise tornado.web.HTTPError(403)

        # authorize the user.
        if not self.authorizer.is_authorized(self, user, "execute", "events"):
            raise tornado.web.HTTPError(403)

    async def get(self, *args, **kwargs):
        """Get an event socket."""
        self.pre_get()
        res = super().get(*args, **kwargs)
        await res

    async def on_message(self, message):
        """Public Tornado method that is called when the client sends a message
        over this connection. This should **not** be overriden by subclasses."""

        # first, verify that the message is an `InlineCompletionRequest`.
        self.log.debug("Message received: %s", message)
        try:
            message = json.loads(message)
            request = InlineCompletionRequest(**message)
        except ValidationError as e:
            self.log.error(e)
            return

        # next, dispatch the request to the correct handler and create the
        # `handle_request` coroutine object
        handle_request = None
        if request.stream:
            try:
                handle_request = self._handle_stream_request(request)
            except NotImplementedError:
                self.log.error(
                    "Unable to handle stream request. The current `InlineCompletionHandler` does not implement the `handle_stream_request()` method."
                )
                return

        else:
            handle_request = self._handle_request(request)

        # finally, wrap `handle_request` in an exception handler, and start the
        # task on the event loop.
        async def handle_request_and_catch():
            try:
                await handle_request
            except Exception as e:
                await self.handle_exc(e, request)

        self.loop.create_task(handle_request_and_catch())

    async def handle_exc(self, e: Exception, request: InlineCompletionRequest):
        """
        Handles an exception raised in either `handle_request()` or
        `handle_stream_request()`. This base class provides a default
        implementation, which may be overridden by subclasses.
        """
        error = CompletionError(
            type=e.__class__.__name__,
            title=e.args[0] if e.args else "Exception",
            traceback=traceback.format_exc(),
        )
        self.reply(
            InlineCompletionReply(
                list=InlineCompletionList(items=[]),
                error=error,
                reply_to=request.number,
            )
        )

    async def _handle_request(self, request: InlineCompletionRequest):
        """Private wrapper around `self.handle_request()`."""
        start = time.time()
        await self.handle_request(request)
        latency_ms = round((time.time() - start) * 1000)
        self.log.info(f"Inline completion handler resolved in {latency_ms} ms.")

    async def _handle_stream_request(self, request: InlineCompletionRequest):
        """Private wrapper around `self.handle_stream_request()`."""
        start = time.time()
        await self.handle_stream_request(request)
        latency_ms = round((time.time() - start) * 1000)
        self.log.info(f"Inline completion streaming completed in {latency_ms} ms.")
