from typing import List, Sequence, Optional

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.pydantic_v1 import BaseModel, Field


class BoundedChatHistory(BaseChatMessageHistory, BaseModel):
    """
    An in-memory implementation of `BaseChatMessageHistory` that stores up to
    `k` exchanges between a user and an LLM.

    For example, when `k=2`, `BoundedChatHistory` will store up to 2 human
    messages and 2 AI messages.
    """

    all_messages: List[BaseMessage] = Field(default_factory=list, alias='messages')
    size: int = 0
    k: int

    @property
    def messages(self) -> List[BaseMessage]:
        return self.all_messages[-self.k * 2 :]

    async def aget_messages(self) -> List[BaseMessage]:
        return self.messages

    def add_message(self, message: BaseMessage) -> None:
        """Add a self-created message to the store"""
        self.all_messages.append(message)

    async def aadd_messages(self, messages: Sequence[BaseMessage]) -> None:
        """Add messages to the store"""
        self.add_messages(messages)

    def clear(self) -> None:
        self.all_messages = []

    async def aclear(self) -> None:
        self.clear()
