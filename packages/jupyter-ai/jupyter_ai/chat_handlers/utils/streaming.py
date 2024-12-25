import time
from typing import Optional

from jupyter_ai.constants import BOT
from jupyterlab_chat.models import Message, NewMessage, User
from jupyterlab_chat.ychat import YChat


class ReplyStreamClosed(Exception):
    pass


class ReplyStream:
    """
    Object yielded by the `BaseChatHandler.start_reply_stream()` context
    manager. This provides three methods:

    - `open() -> str`: Opens a new, empty reply stream. This shows "Jupyternaut
       is writing..." in the chat UI until the stream is closed.
    - `write(chunk: str)`: Appends `chunk` to the reply stream.
    - `close()`: Closes the reply stream.

    Note that `open()` and `close()` are automatically called by the
    `BaseChatHandler.start_reply_stream()` context manager, so only `write()`
    should be called within that context.

    TODO: Re-implement the capability to customize the pending message.

    TODO: Re-implement the capability to add metadata to messages. Message
    metadata is important for some usage scenarios like implementing LLM
    feedback in the UI, which requires some kind of LLM-specific request ID to
    be available in the message metadata.
    """

    def __init__(self, ychat: YChat):
        self.ychat = ychat
        self._is_open = False
        self._stream_id: Optional[str] = None

    def _set_user(self):
        bot = self.ychat.get_user(BOT["username"])
        if not bot:
            self.ychat.set_user(User(**BOT))

    def open(self):
        self._set_user()
        self.ychat.awareness.set_local_state_field("isWriting", True)
        self._is_open = True

    def write(self, chunk: str) -> str:
        """
        Writes a string chunk to the current reply stream. Returns the ID of the
        message that this reply stream is writing to.
        """
        try:
            assert self._is_open
        except:
            raise ReplyStreamClosed("Reply stream must be opened first.") from None

        if not self._stream_id:
            self._set_user()
            self._stream_id = self.ychat.add_message(
                NewMessage(body="", sender=BOT["username"])
            )

        self._set_user()
        self.ychat.update_message(
            Message(
                id=self._stream_id,
                body=chunk,
                time=time.time(),
                sender=BOT["username"],
                raw_time=False,
            ),
            append=True,
        )

        return self._stream_id

    def close(self):
        self.ychat.awareness.set_local_state_field("isWriting", False)
        self._is_open = False
