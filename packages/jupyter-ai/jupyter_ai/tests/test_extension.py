# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import pytest
from jupyter_ai.extension import AiExtension

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
