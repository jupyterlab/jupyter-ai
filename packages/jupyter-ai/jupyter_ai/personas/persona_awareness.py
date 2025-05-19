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
