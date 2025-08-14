from __future__ import annotations
import asyncio
from pathlib import Path
import pytest
from traitlets.config import Config, LoggingConfigurable
import logging
from jupyter_server.services.contents.filemanager import AsyncFileContentsManager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jupyter_server.serverapp import ServerApp

pytest_plugins = ("jupyter_server.pytest_plugin",)

@pytest.fixture
def jp_server_config(jp_server_config, tmp_path):
    return Config({"ServerApp": {"jpserver_extensions": {"jupyter_ai": True}}, "ContentsManager": {"root_dir": str(tmp_path)}})


@pytest.fixture(scope="session")
def static_test_files_dir() -> Path:
    return (
        Path(__file__).parent.resolve()
        / "packages"
        / "jupyter-ai"
        / "jupyter_ai"
        / "tests"
        / "static"
    )

class MockAiExtension(LoggingConfigurable):
    """Mock AiExtension class for testing purposes."""
    
    serverapp: ServerApp

    def __init__(self, *args, serverapp: ServerApp, **kwargs):
        super().__init__(*args, **kwargs)
        self.serverapp = serverapp
        self._log = None
        
    @property
    def log(self) -> logging.Logger:
        return self.serverapp.log
        
    @property
    def event_loop(self) -> asyncio.AbstractEventLoop:
        return self.serverapp.io_loop.asyncio_loop
    
    @property
    def contents_manager(self) -> AsyncFileContentsManager:
        return self.serverapp.contents_manager


@pytest.fixture
def mock_ai_extension(jp_server_config, jp_configurable_serverapp) -> MockAiExtension:
    """
    Returns a mocked `AiExtension` object that can be passed as the `parent`
    argument to objects normally initialized by `AiExtension`. This should be
    passed to most of the "manager singletons" like `ConfigManager`,
    `PersonaManager`, and `EnvSecretsManager`.

    See `MockAiExtension` in `conftest.py` for a complete description of the
    attributes, properties, and methods available. If something is missing,
    please feel free to add to it in your PR.
    
    Returns:
        A `MockAiExtension` instance that can be passed as the `parent` argument
        to objects normally initialized by `AiExtension`.
    """
    serverapp = jp_configurable_serverapp()
    return MockAiExtension(config=jp_server_config, serverapp=serverapp)

