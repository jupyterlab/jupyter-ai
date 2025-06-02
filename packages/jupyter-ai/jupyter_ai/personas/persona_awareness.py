import random
from asyncio import Task, create_task
from contextlib import contextmanager
from dataclasses import asdict
from logging import Logger
from time import time
from typing import TYPE_CHECKING, Any, Optional

from anyio import create_task_group, sleep
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
    dictionary.

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
    _heartbeat: Task | None = None

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

        with self.as_custom_client():
            self.awareness.set_local_state({})

        if self.user:
            self._register_user()

        # Start the awareness heartbeat task
        self._on_awareness_changed("change", None)

        # Observe awareness changes to keep the heartbeat or not, whether there are
        # users (not bot) in the awareness state or not.
        self.awareness.observe(self._on_awareness_changed)

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
        """
        return self.awareness._outdated_timeout

    def _register_user(self):
        if not self.user:
            return

        with self.as_custom_client():
            self.awareness.set_local_state_field("user", asdict(self.user))

    def get_local_state(self) -> Optional[dict[str, Any]]:
        with self.as_custom_client():
            return self.awareness.get_local_state()

    def set_local_state_field(self, field: str, value: Any) -> None:
        with self.as_custom_client():
            self.awareness.set_local_state_field(field, value)

    def _get_time(self) -> int:
        return int(time() * 1000)

    def start(self) -> None:
        """
        Starts the awareness heartbeat task if it is not already running.
        Restore the local state if it is not set, and register the user if available.
        """
        if self._heartbeat:
            self.log.warning(
                f"Awareness heartbeat is already running for {self._custom_client_id} ({self.user.username})."
            )
            return

        if self.get_local_state() is None:
            with self.as_custom_client():
                self.awareness.set_local_state({})

            if self.user:
                self._register_user()

        self._heartbeat = create_task(self._start())

    async def _start(self) -> None:
        """
        Starts the awareness heartbeat task, which periodically renews the state.
        """
        while True:
            await sleep(self.outdated_timeout / 1000 / 10)
            now = self._get_time()
            local_state = self.get_local_state()
            if (
                local_state is not None
                and self.outdated_timeout / 2
                <= now - self.awareness.meta[self._custom_client_id]["lastUpdated"]
            ):
                # renew local clock
                with self.as_custom_client():
                    self.awareness.set_local_state(local_state)

    def stop(self) -> None:
        """
        Stops the awareness heartbeat task if it is running.
        """
        if self._heartbeat:
            self._heartbeat.cancel()
            self._heartbeat = None

    def _on_awareness_changed(self, topic, changes) -> None:
        """
        Callback method called when the awareness state changes.
        Check if there are still users in the awareness state, and if not,
        stop updating the personna awareness state.
        """
        if not topic == "change":
            return

        states = self.awareness.states
        should_be_started = False
        for state in states.values():
            if "user" in state and (
                not "bot" in state["user"] or not state["user"]["bot"]
            ):
                should_be_started = True
                break

        if should_be_started and not self._heartbeat:
            self.start()
        elif not should_be_started and self._heartbeat:
            self.stop()
