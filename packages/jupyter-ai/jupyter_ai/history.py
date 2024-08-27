import time
from typing import List, Sequence

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.pydantic_v1 import BaseModel, PrivateAttr

from .models import HumanChatMessage


class BoundedChatHistory(BaseChatMessageHistory, BaseModel):
    """
    An in-memory implementation of `BaseChatMessageHistory` that stores up to
    `k` exchanges between a user and an LLM.

    For example, when `k=2`, `BoundedChatHistory` will store up to 2 human
    messages and 2 AI messages.
    """

    k: int
    clear_time: float = 0.0
    _all_messages: List[BaseMessage] = PrivateAttr(default_factory=list)

    @property
    def messages(self) -> List[BaseMessage]:
        return self._all_messages[-self.k * 2 :]

    async def aget_messages(self) -> List[BaseMessage]:
        return self.messages

    def add_message(self, message: BaseMessage) -> None:
        """Add a self-created message to the store"""
        self._all_messages.append(message)

    async def aadd_messages(self, messages: Sequence[BaseMessage]) -> None:
        """Add messages to the store"""
        self.add_messages(messages)

    def clear(self) -> None:
        self._all_messages = []
        self.clear_time = time.time()

    async def aclear(self) -> None:
        self.clear()


class WrappedBoundedChatHistory(BaseChatMessageHistory, BaseModel):
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

    history: BoundedChatHistory
    last_human_msg: HumanChatMessage

    @property
    def messages(self) -> List[BaseMessage]:
        return self.history.messages

    def add_message(self, message: BaseMessage) -> None:
        """Prevent adding messages to the store if clear was triggered."""
        if self.last_human_msg.time > self.history.clear_time:
            self.history.add_message(message)

    async def aadd_messages(self, messages: Sequence[BaseMessage]) -> None:
        self.add_messages(messages)

    def clear(self) -> None:
        self.history.clear()
