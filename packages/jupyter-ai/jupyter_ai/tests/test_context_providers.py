import logging
from unittest import mock

import pytest
from jupyter_ai.config_manager import ConfigManager
from jupyter_ai.context_providers import FileContextProvider, find_commands
from jupyter_ai.history import BoundedChatHistory
from jupyter_ai.models import ChatClient, HumanChatMessage, Persona


@pytest.fixture
def human_chat_message() -> HumanChatMessage:
    chat_client = ChatClient(
        id=0, username="test", initials="test", name="test", display_name="test"
    )
    prompt = (
        "@file:test1.py @file @file:dir/test2.md test test\n"
        "@file:/dir/test3.png\n"
        "test@file:fail1.py\n"
        "@file:dir\\ test\\ /test\\ 4.py\n"  # spaces with escape
        "@file:'test 5.py' @file:\"test6 .py\"\n"  # quotes with spaces
        "@file:'test7.py test\"\n"  # do not allow for mixed quotes
        "```\n@file:fail2.py\n```\n"  # do not look within backticks
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
    expected = [
        "@file:test1.py",
        "@file:dir/test2.md",
        "@file:/dir/test3.png",
        r"@file:dir\ test\ /test\ 4.py",
        "@file:'test 5.py'",
        '@file:"test6 .py"',
        "@file:'test7.py",
    ]
    commands = [
        cmd.cmd
        for cmd in find_commands(file_context_provider, human_chat_message.prompt)
    ]
    assert commands == expected


def test_replace_prompt(file_context_provider, human_chat_message):
    expected = (
        "'test1.py' @file 'dir/test2.md' test test\n"
        "'/dir/test3.png'\n"
        "test@file:fail1.py\n"
        "'dir test /test 4.py'\n"
        "'test 5.py' 'test6 .py'\n"
        "'test7.py' test\"\n"
        "```\n@file:fail2.py\n```\n"  # do not look within backticks
    )
    prompt = file_context_provider.replace_prompt(human_chat_message.prompt)
    assert prompt == expected
