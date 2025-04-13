from jupyterlab_chat.ychat import YChat
from jupyterlab_chat.models import User
from pycrdt import Awareness
import random
from dataclasses import asdict
from logging import Logger
from typing import Any, Optional, TYPE_CHECKING

from contextlib import contextmanager

if TYPE_CHECKING:
    from collections.abc import Iterator

TEST_USER = User(
    username="jupyter-ai:superjupyter",
    name="SuperJupyter",
    display_name="SuperJupyter",
    avatar_url="/api/ai/static/jupyternaut.svg",
)

class PersonaAwareness:
    """
    Custom helper class that accepts a `YChat` instance and returns a
    `pycrdt.Awareness`-like interface, with a custom client ID scoped to this
    instance. This class implements a subset of the methods provided by
    `pycrdt.Awareness`.

    - This class optionally accepts a `User` object in the constructor. When
    passed, this class will automatically register this user in the YChat and
    awareness dictionaries, via `ychat.set_user()` and
    `awareness.set_local_state()` respectively.

    - This class works by manually setting `ydoc.awareness.client_id` before &
    after each method call. This class provides a `self.as_custom_client()`
    context manager that automatically does this upon enter & exit.
    
    - This class is required to provide awareness states for >1 persona, because
    `pycrdt` doesn't provide a way to set the awareness state for more than one
    client ID (for now).
    """

    ychat: YChat
    awareness: Awareness
    user: Optional[User]

    _original_client_id: int
    _custom_client_id: int

    def __init__(self, *, ychat: YChat, log: Logger, user: Optional[User]):
        self.ychat = ychat
        self.awareness = ychat.awareness
        self.user = user
        self._original_client_id = self.awareness.client_id
        self._custom_client_id = random.getrandbits(32)

        with self.as_custom_client():
            self.awareness.set_local_state({})

        if self.user:
            self._register_user()
    
    @contextmanager
    def as_custom_client(self) -> 'Iterator[None]':
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
            self.ychat.set_user(self.user)
            self.awareness.set_local_state_field('user', asdict(self.user))
    
    def get_local_state(self) -> dict[str, Any]:
        with self.as_custom_client():
            return self.awareness.get_local_state()
        
    def set_local_state_field(self, field: str, value: Any) -> None:
        with self.as_custom_client():
            return self.awareness.set_local_state_field(field, value)
    