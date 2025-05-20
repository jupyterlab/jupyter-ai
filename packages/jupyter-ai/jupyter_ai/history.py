from typing import Optional

from jupyterlab_chat.models import Message as JChatMessage
from jupyterlab_chat.ychat import YChat
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


class YChatHistory(BaseChatMessageHistory):
    """
    An implementation of `BaseChatMessageHistory` that returns the preceding `k`
    exchanges (`k * 2` messages) from the given YChat model.

    If `k` is set to `None`, then this class returns all preceding messages.

    TODO: Consider just defining `k` as the number of messages and default to 4.
    """

    def __init__(self, ychat: YChat, k: Optional[int] = None):
        self.ychat = ychat
        self.k = k

    @property
    def messages(self) -> list[BaseMessage]:  # type:ignore[override]
        """
        Returns the last `2 * k` messages preceding the latest message. If
        `k` is set to `None`, return all preceding messages.
        """
        # TODO: consider bounding history based on message size (e.g. total
        # char/token count) instead of message count.
        all_messages = self.ychat.get_messages()

        # gather last k * 2 messages and return
        # we exclude the last message since that is the human message just
        # submitted by a user.
        start_idx = 0 if self.k is None else -2 * self.k - 1
        recent_messages: list[JChatMessage] = all_messages[start_idx:-1]

        return self._convert_to_langchain_messages(recent_messages)

    def _convert_to_langchain_messages(self, jchat_messages: list[JChatMessage]):
        """
        Accepts a list of Jupyter Chat messages, and returns them as a list of
        LangChain messages.
        """
        messages: list[BaseMessage] = []
        for jchat_message in jchat_messages:
            if jchat_message.sender.startswith("jupyter-ai-personas::"):
                messages.append(AIMessage(content=jchat_message.body))
            else:
                messages.append(HumanMessage(content=jchat_message.body))

        return messages

    def add_message(self, message: BaseMessage) -> None:
        # do nothing when other LangChain objects call this method, since
        # message history is maintained by the `YChat` shared document.
        return

    def clear(self):
        raise NotImplementedError()
