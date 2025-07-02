import asyncio
import random
from contextlib import contextmanager
from dataclasses import asdict
from logging import Logger
from typing import TYPE_CHECKING, Any, Optional

from jupyterlab_chat.models import User
from jupyterlab_chat.ychat import YChat
from pycrdt import Awareness

if TYPE_CHECKING:
    from collections.abc import Iterator


class PersonaAwareness:
    """
    Custom helper class that accepts a `YChat` instance and returns a
    `pycrdt.Awareness`-like interface, with a custom client ID scoped to this
    instance. This class implements a subset of the methods provided by
    `pycrdt.Awareness`.

    - This class optionally accepts a `User` object in the constructor. When
    passed, this class will automatically register this user in the awareness
    dictionary on init.

    - This class works by manually setting `ydoc.awareness.client_id` before &
    after each method call. This class provides a `self.as_custom_client()`
    context manager that automatically does this upon enter & exit.

    - This class is required to provide awareness states for >1 persona, because
    `pycrdt.Awareness` doesn't provide a way to set the awareness state for >1
    client ID (for now).
    """

    awareness: Awareness
    log: Logger
    user: Optional[User]

    _original_client_id: int
    _custom_client_id: int
    _heartbeat_task: asyncio.Task

    def __init__(self, *, ychat: YChat, log: Logger, user: Optional[User]):
        # Bind instance attributes
        self.log = log
        self.user = user

        # Bind awareness object if available, initialize it otherwise
        if ychat.awareness:
            self.awareness = ychat.awareness
        else:
            self.awareness = Awareness(ydoc=ychat._ydoc)

        # Initialize a custom client ID & save the original client ID
        self._original_client_id = self.awareness.client_id
        self._custom_client_id = random.getrandbits(32)

        # Initialize local awareness state using the custom client ID
        self.set_local_state({})
        if self.user:
            self._register_user()

        # Start the awareness heartbeat task
        self._heartbeat_task = asyncio.create_task(self._start_heartbeat())

    @contextmanager
    def as_custom_client(self) -> "Iterator[None]":
        """
        Context manager that automatically:

        - Sets the awareness client ID to the custom client ID created by this
        instance upon entering.

        - Resets the awareness client ID back to the original client ID upon
        exiting.
        """
        self.awareness.client_id = self._custom_client_id
        try:
            yield
        finally:
            self.awareness.client_id = self._original_client_id

    @property
    def outdated_timeout(self) -> int:
        """
        Returns the outdated timeout of the document awareness, in milliseconds.
        The timeout value should be 30000 milliseconds (30 seconds), according to the
        default value in `y-protocols.awareness` and `pycrdt.Awareness`.
        - https://github.com/yjs/y-protocols/blob/2d8cd5c06b3925fbf9b5215dc341f8096a0a8d5c/awareness.js#L13
        - https://github.com/y-crdt/pycrdt/blob/e269a3e63ad7986a3349e2d2bc7bd5f0dfca9c79/python/pycrdt/_awareness.py#L23
        """
        return self.awareness._outdated_timeout

    def _register_user(self):
        if not self.user:
            return

        with self.as_custom_client():
            self.awareness.set_local_state_field("user", asdict(self.user))

    def get_local_state(self) -> Optional[dict[str, Any]]:
        """
        Returns the local state of the awareness instance.
        """
        with self.as_custom_client():
            return self.awareness.get_local_state()

    def set_local_state(self, state: Optional[dict[str, Any]]) -> None:
        """
        Sets the local state of this persona in the awareness map, indexed by
        this instance's custom client ID.

        Passing `state=None` deletes the local state indexed by this instance's
        custom client ID.
        """
        with self.as_custom_client():
            self.awareness.set_local_state(state)

    def set_local_state_field(self, field: str, value: Any) -> None:
        """
        Sets a specific field in the local state of the awareness instance.
        """
        with self.as_custom_client():
            self.awareness.set_local_state_field(field, value)

    async def _start_heartbeat(self):
        """
        Background task that updates this instance's local state every
        `0.8 * self.outdated_timeout` milliseconds. `pycrdt` and `yjs`
        automatically disconnect clients if they do not make updates in
        a long time (default: 30000 ms). This task keeps personas alive
        after 30 seconds of no usage in each chat session.
        """
        while True:
            await asyncio.sleep(0.8 * self.outdated_timeout / 1000)
            local_state = self.get_local_state() or {}
            self.set_local_state(local_state)

    def shutdown(self) -> None:
        """
        Stops this instance's background tasks and removes the persona's custom
        client ID from the awareness map.
        """
        self._heartbeat_task.cancel()
        self.set_local_state(None)
