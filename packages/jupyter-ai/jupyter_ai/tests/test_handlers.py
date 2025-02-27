import logging
import os
import stat
from typing import Optional
from unittest import mock

import pytest
from jupyter_ai.chat_handlers import DefaultChatHandler, learn
from jupyter_ai.config_manager import ConfigManager
from jupyter_ai.extension import DEFAULT_HELP_MESSAGE_TEMPLATE
from jupyter_ai.handlers import RootChatHandler
from jupyter_ai.history import BoundedChatHistory
from jupyter_ai.models import (
    ChatClient,
    ClosePendingMessage,
    HumanChatMessage,
    Message,
    PendingMessage,
    Persona,
)
from jupyter_ai_magics import BaseProvider
from langchain_community.llms import FakeListLLM
from tornado.httputil import HTTPServerRequest
from tornado.web import Application


class MockLearnHandler(learn.LearnChatHandler):
    def __init__(self):
        pass


class MockProvider(BaseProvider, FakeListLLM):
    id = "my_provider"
    name = "My Provider"
    model_id_key = "model"
    models = ["model"]
    should_raise: Optional[bool] = None

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
        self.request = HTTPServerRequest()
        self.application = Application()
        self.messages = []
        self.tasks = []
        config_manager = mock.create_autospec(ConfigManager)
        config_manager.lm_provider = lm_provider or MockProvider
        config_manager.lm_provider_params = lm_provider_params or {"model_id": "model"}
        config_manager.persona = Persona(name="test", avatar_route="test")

        def broadcast_message(message: Message) -> None:
            self.messages.append(message)

        root_handler = mock.create_autospec(RootChatHandler)
        root_handler.broadcast_message = broadcast_message

        super().__init__(
            log=logging.getLogger(__name__),
            config_manager=config_manager,
            root_chat_handlers={"root": root_handler},
            model_parameters={},
            chat_history=[],
            llm_chat_memory=BoundedChatHistory(k=2),
            root_dir="",
            preferred_dir="",
            dask_client_future=None,
            help_message_template=DEFAULT_HELP_MESSAGE_TEMPLATE,
            chat_handlers={},
            context_providers={},
            message_interrupted={},
            log_dir="",
        )


class TestException(Exception):
    pass


@pytest.fixture
def chat_client():
    return ChatClient(
        id="test-client-uuid",
        username="test",
        initials="test",
        name="test",
        display_name="test",
    )


@pytest.fixture
def human_chat_message(chat_client):
    return HumanChatMessage(
        id="test",
        time=0,
        body="test message",
        prompt="test message",
        client=chat_client,
    )


def test_learn_index_permissions(tmp_path):
    test_dir = tmp_path / "test"
    with mock.patch.object(learn, "INDEX_SAVE_DIR", new=test_dir):
        handler = MockLearnHandler()
        handler._ensure_dirs()
        mode = os.stat(test_dir).st_mode
        assert stat.filemode(mode) == "drwx------"


async def test_default_closes_pending_on_success(human_chat_message):
    handler = TestDefaultChatHandler(
        lm_provider=MockProvider,
        lm_provider_params={
            "model_id": "model",
            "should_raise": False,
        },
    )
    await handler.process_message(human_chat_message)

    # >=2 because there are additional stream messages that follow
    assert len(handler.messages) >= 2
    assert isinstance(handler.messages[0], PendingMessage)
    assert isinstance(handler.messages[1], ClosePendingMessage)


async def test_default_closes_pending_on_error(human_chat_message):
    handler = TestDefaultChatHandler(
        lm_provider=MockProvider,
        lm_provider_params={
            "model_id": "model",
            "should_raise": True,
        },
    )
    with pytest.raises(TestException):
        await handler.process_message(human_chat_message)

    assert len(handler.messages) == 2
    assert isinstance(handler.messages[0], PendingMessage)
    assert isinstance(handler.messages[1], ClosePendingMessage)


async def test_sends_closing_message_at_most_once(human_chat_message):
    handler = TestDefaultChatHandler(
        lm_provider=MockProvider,
        lm_provider_params={
            "model_id": "model",
            "should_raise": False,
        },
    )
    message = handler.start_pending("Flushing Pipe Network")
    assert len(handler.messages) == 1
    assert isinstance(handler.messages[0], PendingMessage)
    assert not message.closed

    handler.close_pending(message)
    assert len(handler.messages) == 2
    assert isinstance(handler.messages[1], ClosePendingMessage)
    assert message.closed

    # closing an already closed message does not lead to another broadcast
    handler.close_pending(message)
    assert len(handler.messages) == 2
    assert message.closed


# TODO
# import json


# async def test_get_example(jp_fetch):
#     # When
#     response = await jp_fetch("jupyter-ai", "get_example")

#     # Then
#     assert response.code == 200
#     payload = json.loads(response.body)
#     assert payload == {
#         "data": "This is /jupyter-ai/get_example endpoint!"
#     }
