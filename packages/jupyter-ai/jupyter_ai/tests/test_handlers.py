import logging
import os
import stat
from typing import List, Optional
from unittest import mock

from jupyter_ai.chat_handlers import DefaultChatHandler, learn
from jupyter_ai.config_manager import ConfigManager
from jupyter_ai.extension import DEFAULT_HELP_MESSAGE_TEMPLATE
from jupyter_ai.history import YChatHistory
from jupyter_ai.models import Persona
from jupyter_ai_magics import BaseProvider
from jupyterlab_chat.models import NewMessage
from jupyterlab_chat.ychat import YChat
from langchain_community.llms import FakeListLLM
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pycrdt import Awareness, Doc


class MockLearnHandler(learn.LearnChatHandler):
    def __init__(self):
        pass


class MockProvider(BaseProvider, FakeListLLM):
    id = "my_provider"
    name = "My Provider"
    model_id_key = "model"
    models = ["model"]
    should_raise: Optional[bool]

    def __init__(self, **kwargs):
        if "responses" not in kwargs:
            kwargs["responses"] = ["Test response"]
        super().__init__(**kwargs)

    def astream(self, *args, **kwargs):
        if self.should_raise:
            raise TestException()
        return super().astream(*args, **kwargs)


class TestDefaultChatHandler(DefaultChatHandler):
    def __init__(self, lm_provider=None, lm_provider_params=None):
        # initialize dummy YDoc, YAwareness, YChat, and YChatHistory objects
        ydoc = Doc()
        awareness = Awareness(ydoc=ydoc)
        self.ychat = YChat(ydoc=ydoc, awareness=awareness)
        self.ychat_history = YChatHistory(ychat=self.ychat)

        # initialize & configure mock ConfigManager
        config_manager = mock.create_autospec(ConfigManager)
        config_manager.lm_provider = lm_provider or MockProvider
        config_manager.lm_provider_params = lm_provider_params or {"model_id": "model"}
        config_manager.persona = Persona(name="test", avatar_route="test")

        super().__init__(
            log=logging.getLogger(__name__),
            config_manager=config_manager,
            model_parameters={},
            root_dir="",
            preferred_dir="",
            dask_client_future=None,
            help_message_template=DEFAULT_HELP_MESSAGE_TEMPLATE,
            chat_handlers={},
            context_providers={},
            message_interrupted={},
            llm_chat_memory=self.ychat_history,
            ychat=self.ychat,
        )

    @property
    def messages(self) -> List[BaseMessage]:
        """
        Test helper method for getting the complete message history, including
        the last message.
        """

        return self.ychat_history._convert_to_langchain_messages(
            self.ychat.get_messages()
        )

    async def send_human_message(self, body: str = "Hello!"):
        """
        Test helper method that sends a human message to this chat handler.

        Without the event subscription performed by `AiExtension`, the chat
        handler is not called automatically, hence we trigger it manually by
        invoking `on_message()`.
        """

        id = self.ychat.add_message(NewMessage(body=body, sender="fake-user-uuid"))
        message = self.ychat.get_message(id)
        return await self.on_message(message)

    @property
    def is_writing(self) -> bool:
        """
        Returns whether Jupyternaut is indicating that it is still writing in
        the chat, based on its Yjs awareness.
        """
        return self.ychat.awareness.get_local_state()["isWriting"]


class TestException(Exception):
    pass


def test_learn_index_permissions(tmp_path):
    test_dir = tmp_path / "test"
    with mock.patch.object(learn, "INDEX_SAVE_DIR", new=test_dir):
        handler = MockLearnHandler()
        handler._ensure_dirs()
        mode = os.stat(test_dir).st_mode
        assert stat.filemode(mode) == "drwx------"


async def test_default_stops_writing_on_success():
    handler = TestDefaultChatHandler(
        lm_provider=MockProvider,
        lm_provider_params={
            "model_id": "model",
            "should_raise": False,
        },
    )
    await handler.send_human_message()
    assert len(handler.messages) == 2
    assert isinstance(handler.messages[0], HumanMessage)
    assert isinstance(handler.messages[1], AIMessage)
    assert not handler.is_writing


async def test_default_stops_writing_on_error():
    handler = TestDefaultChatHandler(
        lm_provider=MockProvider,
        lm_provider_params={
            "model_id": "model",
            "should_raise": True,
        },
    )
    await handler.send_human_message()
    print(handler.messages)
    assert len(handler.messages) == 2
    assert isinstance(handler.messages[0], HumanMessage)
    assert isinstance(handler.messages[1], AIMessage)
    assert not handler.is_writing
