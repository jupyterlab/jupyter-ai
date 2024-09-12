import logging
from unittest import mock

import pytest
from jupyter_ai.context_providers import FileContextProvider
from jupyter_ai.config_manager import ConfigManager
from jupyter_ai.history import BoundedChatHistory
from jupyter_ai.models import (
    ChatClient,
    HumanChatMessage,
    Persona,
)


@pytest.fixture
def human_chat_message() -> HumanChatMessage:
    chat_client = ChatClient(
        id=0, username="test", initials="test", name="test", display_name="test"
    )
    prompt = (
        "@file:test1.py @file @file:dir/test2.md test test\n"
        "@file:/dir/test3.png test@file:test4.py"
    )
    return HumanChatMessage(
        id="test",
        time=0,
        body=prompt,
        prompt=prompt,
        client=chat_client,
    )


@pytest.fixture
def file_context_provider() -> FileContextProvider:
    config_manager = mock.create_autospec(ConfigManager)
    config_manager.persona = Persona(name="test", avatar_route="test")
    return FileContextProvider(
        log=logging.getLogger(__name__),
        config_manager=config_manager,
        model_parameters={},
        chat_history=[],
        llm_chat_memory=BoundedChatHistory(k=2),
        root_dir="",
        preferred_dir="",
        dask_client_future=None,
        chat_handlers={},
        context_providers={},
    )


def test_find_instances(file_context_provider, human_chat_message):
    expected = ["@file:test1.py", "@file:dir/test2.md", "@file:/dir/test3.png"]
    instances = file_context_provider._find_instances(human_chat_message.prompt)
    assert instances == expected


def test_replace_prompt(file_context_provider, human_chat_message):
    expected = (
        "'test1.py' @file 'dir/test2.md' test test\n"
        "'/dir/test3.png' test@file:test4.py"
    )
    prompt = file_context_provider.replace_prompt(human_chat_message.prompt)
    assert prompt == expected
