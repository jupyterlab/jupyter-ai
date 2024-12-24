import logging
from unittest import mock

import pytest
from jupyter_ai.config_manager import ConfigManager
from jupyter_ai.context_providers import FileContextProvider, find_commands
from jupyter_ai.models import Persona
from jupyterlab_chat.models import Message


@pytest.fixture
def human_message() -> Message:
    prompt = (
        "@file:test1.py @file @file:dir/test2.md test test\n"
        "@file:/dir/test3.png\n"
        "test@file:fail1.py\n"
        "@file:dir\\ test\\ /test\\ 4.py\n"  # spaces with escape
        "@file:'test 5.py' @file:\"test6 .py\"\n"  # quotes with spaces
        "@file:'test7.py test\"\n"  # do not allow for mixed quotes
        "```\n@file:fail2.py\n```\n"  # do not look within backticks
    )
    return Message(id="fake-message-uuid", time=0, body=prompt, sender="fake-user-uuid")


@pytest.fixture
def file_context_provider() -> FileContextProvider:
    config_manager = mock.create_autospec(ConfigManager)
    config_manager.persona = Persona(name="test", avatar_route="test")
    return FileContextProvider(
        log=logging.getLogger(__name__),
        config_manager=config_manager,
        model_parameters={},
        root_dir="",
        preferred_dir="",
        dask_client_future=None,
        context_providers={},
    )


def test_find_instances(file_context_provider, human_message):
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
        cmd.cmd for cmd in find_commands(file_context_provider, human_message.body)
    ]
    assert commands == expected


def test_replace_prompt(file_context_provider, human_message):
    expected = (
        "'test1.py' @file 'dir/test2.md' test test\n"
        "'/dir/test3.png'\n"
        "test@file:fail1.py\n"
        "'dir test /test 4.py'\n"
        "'test 5.py' 'test6 .py'\n"
        "'test7.py' test\"\n"
        "```\n@file:fail2.py\n```\n"  # do not look within backticks
    )
    prompt = file_context_provider.replace_prompt(human_message.body)
    assert prompt == expected
