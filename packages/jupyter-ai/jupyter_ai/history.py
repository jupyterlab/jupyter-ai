import time
from collections.abc import Sequence
from typing import Optional

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

from .models import HumanChatMessage

HUMAN_MSG_ID_KEY = "_jupyter_ai_human_msg_id"


class BoundedChatHistory(BaseChatMessageHistory):
    """
    An in-memory implementation of `BaseChatMessageHistory` that stores up to
    `k` exchanges between a user and an LLM.

    For example, when `k=2`, `BoundedChatHistory` will store up to 2 human
    messages and 2 AI messages. If `k` is set to `None` all messages are kept.
    """

    def __init__(
        self,
        k: Optional[int] = None,
        clear_time: float = 0.0,
        cleared_msgs: set[str] = set(),
    ):
        self.k = k
        self.clear_time = clear_time
        self.cleared_msgs = cleared_msgs
        self._all_messages: list[BaseMessage] = []

    @property
    def messages(self) -> list[BaseMessage]:  # type:ignore[override]
        if self.k is None:
            return self._all_messages
        return self._all_messages[-self.k * 2 :]

    async def aget_messages(self) -> list[BaseMessage]:
        return self.messages

    def add_message(self, message: BaseMessage) -> None:
        """Add a self-created message to the store"""
        if HUMAN_MSG_ID_KEY not in message.additional_kwargs:
            # human message id must be added to allow for targeted clearing of messages.
            # `WrappedBoundedChatHistory` should be used instead to add messages.
            raise ValueError(
                "Message must have a human message ID to be added to the store."
            )
        self._all_messages.append(message)

    async def aadd_messages(self, messages: Sequence[BaseMessage]) -> None:
        """Add messages to the store"""
        self.add_messages(messages)

    def clear(self, human_msg_ids: Optional[list[str]] = None) -> None:
        """Clears conversation exchanges. If `human_msg_id` is provided, only
        clears the respective human message and its reply. Otherwise, clears
        all messages."""
        if human_msg_ids:
            self._all_messages = [
                m
                for m in self._all_messages
                if m.additional_kwargs[HUMAN_MSG_ID_KEY] not in human_msg_ids
            ]
            self.cleared_msgs.update(human_msg_ids)
        else:
            self._all_messages = []
            self.cleared_msgs = set()
            self.clear_time = time.time()

    async def aclear(self) -> None:
        self.clear()


class WrappedBoundedChatHistory(BaseChatMessageHistory):
    """
    Wrapper around `BoundedChatHistory` that only appends an `AgentChatMessage`
    if the `HumanChatMessage` it is replying to was not cleared. If a chat
    handler is replying to a `HumanChatMessage`, it should pass this object via
    the `last_human_msg` configuration parameter.

    For example, a chat handler that is streaming a reply to a
    `HumanChatMessage` should be called via:

    ```py
    async for chunk in self.llm_chain.astream(
        {"input": message.body},
        config={"configurable": {"last_human_msg": message}},
    ):
        ...
    ```

    Reference: https://python.langchain.com/v0.1/docs/expression_language/how_to/message_history/
    """

    def __init__(
        self,
        history: BoundedChatHistory,
        last_human_msg: HumanChatMessage,
        *args,
        **kwargs,
    ):
        self.history = history
        self.last_human_msg = last_human_msg
        super().__init__(*args, **kwargs)

    @property
    def messages(self) -> list[BaseMessage]:  # type:ignore[override]
        return self.history.messages

    def add_message(self, message: BaseMessage) -> None:
        # prevent adding pending messages to the store if clear was triggered.
        if (
            self.last_human_msg.time > self.history.clear_time
            and self.last_human_msg.id not in self.history.cleared_msgs
        ):
            message.additional_kwargs[HUMAN_MSG_ID_KEY] = self.last_human_msg.id
            self.history.add_message(message)

    async def aadd_messages(self, messages: Sequence[BaseMessage]) -> None:
        self.add_messages(messages)

    def clear(self) -> None:
        self.history.clear()
