# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from unittest import mock

import pytest
from jupyter_ai.extension import AiExtension
from jupyter_ai.history import HUMAN_MSG_ID_KEY
from jupyter_ai_magics import BaseProvider
from langchain_core.messages import BaseMessage

pytest_plugins = ["pytest_jupyter.jupyter_server"]

KNOWN_LM_A = "openai"
KNOWN_LM_B = "huggingface_hub"


@pytest.mark.parametrize(
    "argv",
    [
        ["--AiExtension.blocked_providers", KNOWN_LM_B],
        ["--AiExtension.allowed_providers", KNOWN_LM_A],
    ],
)
@pytest.mark.skip(
    reason="Reads from user's config file instead of an isolated one. Causes test flakiness during local development."
)
def test_allows_providers(argv, jp_configurable_serverapp):
    server = jp_configurable_serverapp(argv=argv)
    ai = AiExtension()
    ai._link_jupyter_server_extension(server)
    ai.initialize_settings()
    assert KNOWN_LM_A in ai.settings["lm_providers"]


@pytest.mark.parametrize(
    "argv",
    [
        ["--AiExtension.blocked_providers", KNOWN_LM_A],
        ["--AiExtension.allowed_providers", KNOWN_LM_B],
    ],
)
@pytest.mark.skip(
    reason="Reads from user's config file instead of an isolated one. Causes test flakiness during local development."
)
def test_blocks_providers(argv, jp_configurable_serverapp):
    server = jp_configurable_serverapp(argv=argv)
    ai = AiExtension()
    ai._link_jupyter_server_extension(server)
    ai.initialize_settings()
    assert KNOWN_LM_A not in ai.settings["lm_providers"]


@pytest.fixture
def jp_server_config(jp_server_config):
    # Disable the extension during server startup to avoid double initialization
    return {"ServerApp": {"jpserver_extensions": {"jupyter_ai": False}}}


@pytest.fixture
def ai_extension(jp_serverapp):
    ai = AiExtension()
    # `BaseProvider.server_settings` can be only initialized once; however, the tests
    # may run in parallel setting it with race condition; because we are not testing
    # the `BaseProvider.server_settings` here, we can just mock the setter
    settings_mock = mock.PropertyMock()
    with mock.patch.object(BaseProvider, "server_settings", settings_mock):
        yield ai


@pytest.mark.parametrize(
    "max_history,messages_to_add,expected_size",
    [
        # for max_history = 1 we expect to see up to 2 messages (1 human and 1 AI message)
        (1, 4, 2),
        # if there is less than `max_history` messages, all should be returned
        (1, 1, 1),
        # if no limit is set, all messages should be returned
        (None, 9, 9),
    ],
)
def test_max_chat_history(ai_extension, max_history, messages_to_add, expected_size):
    ai = ai_extension
    ai.default_max_chat_history = max_history
    ai.initialize_settings()
    for i in range(messages_to_add):
        message = BaseMessage(
            content=f"Test message {i}",
            type="test",
            additional_kwargs={HUMAN_MSG_ID_KEY: f"message-{i}"},
        )
        ai.settings["llm_chat_memory"].add_message(message)

    assert len(ai.settings["llm_chat_memory"].messages) == expected_size
