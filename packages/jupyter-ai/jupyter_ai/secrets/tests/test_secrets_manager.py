"""
Unit tests for the `..secrets_manager` module.
"""

from __future__ import annotations
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import TYPE_CHECKING
import os

from jupyter_ai.secrets.secrets_manager import EnvSecretsManager
from jupyter_ai.secrets.secrets_types import SecretsList

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def dotenv_path(tmp_path):
    """
    Returns the expected path of the `.env` file managed by the `manager`
    fixture.
    """
    return tmp_path / ".env"


@pytest.fixture
def manager(mock_ai_extension, dotenv_path):
    """
    Returns the configured `EnvSecretsManager` instance to be tested in this
    file.
    """
    # Yield configured `EnvSecretsManager`
    manager = EnvSecretsManager(parent=mock_ai_extension)
    yield manager

    # Cleanup
    manager.stop()
    try:
        os.remove(dotenv_path)
    except:
        pass


class TestEnvSecretsManager():
    """
    Unit tests for the EnvSecretsManager.

    At the start of each test, no secrets are set in the environment variables
    passed to the process and no `.env` file is set.
    """
    
    def test_initial_state(self, manager: EnvSecretsManager, dotenv_path: Path):
        """
        ASSERTS: 
        
        1. `list_secrets()` returns an empty `SecretsList` response.

        2. No `.env` file is created.
        """
        # Assertion 1
        response = manager.list_secrets()
        assert isinstance(response, SecretsList)
        assert response.static_secrets == []
        assert response.editable_secrets == []

        # Assertion 2
        assert not os.path.exists(dotenv_path)
    
    async def test_adding_secrets_via_manager(self, manager: EnvSecretsManager, dotenv_path: Path):
        """
        ASSERTS:
        
        1. Adding a secret via `update_secret()` creates a `.env` file
        under `tmp_path`.

        2. Adding another secret results in 2 secrets listed in `.env`.

        3. `list_secrets()` lists the 2 newly added secrets as editable secrets.

        4. Both secrets are set in `os.environ`.
        """
        # Assertion 1
        await manager.update_secrets({
            "NEW_API_KEY": "some_value"
        })
        assert os.path.exists(dotenv_path)
        with open(dotenv_path) as f:
            content = f.read()
        assert content.strip() == 'NEW_API_KEY="some_value"'

        # Assertion 2
        await manager.update_secrets({
            "ANOTHER_API_KEY": "some_value"
        })
        with open(dotenv_path) as f:
            content = f.read()
        lines = content.strip().splitlines()
        assert 'NEW_API_KEY="some_value"' in lines
        assert 'ANOTHER_API_KEY="some_value"' in lines

        # Assertion 3
        list_secrets_response = manager.list_secrets()
        assert list_secrets_response.static_secrets == []
        assert list_secrets_response.editable_secrets == sorted([
            "NEW_API_KEY",
            "ANOTHER_API_KEY"
        ])

        # Assertion 4
        assert os.environ["NEW_API_KEY"] == "some_value"
        assert os.environ["ANOTHER_API_KEY"] == "some_value"
    
    async def test_updating_secrets_via_manager(self, manager: EnvSecretsManager, dotenv_path: Path):
        """
        ASSERTS: 
        
        1. A previously added secret can be updated.
        
        2. Only a single secret is listed in the `.env` file and the
        `list_secrets()` response.

        3. The new value is set in `os.environ`.
        """
        # Assertion 1
        await manager.update_secrets({
            "API_KEY": "old_value"
        })
        assert os.environ["API_KEY"] == "old_value"
        await manager.update_secrets({
            "API_KEY": "new_value"
        })

        # Assertion 2
        with open(dotenv_path) as f:
            content = f.read()
        assert content.strip() == 'API_KEY="new_value"'
        assert manager.list_secrets().static_secrets == []
        assert manager.list_secrets().editable_secrets == ["API_KEY"]

        # Assertion 3
        assert os.environ["API_KEY"] == "new_value"
        
    
    async def test_adding_secrets_via_dotenv(self, manager: EnvSecretsManager, dotenv_path: Path):
        """
        ASSERTS: 
        
        1. After creating a new `.env` file with secrets and waiting a few
        seconds, the secrets manager lists secrets from the new `.env` file.

        2. The new secrets are set in `os.environ`.
        """
        # Assertion 1
        with open(dotenv_path, "w") as f:
            f.write('API_KEY_1="api_key_1_value"\n')
            f.write('API_KEY_2="api_key_2_value"\n')
        await asyncio.sleep(3)
        assert manager.list_secrets().static_secrets == []
        assert manager.list_secrets().editable_secrets == ["API_KEY_1", "API_KEY_2"]

        # Assertion 2
        assert os.environ["API_KEY_1"] == "api_key_1_value"
        assert os.environ["API_KEY_2"] == "api_key_2_value"

    async def test_updating_secrets_via_dotenv(self, manager: EnvSecretsManager, dotenv_path: Path):
        """
        ASSERTS: After updating an existing `.env` file directly (i.e. through the
        filesystem and not the secrets manager) and waiting a few seconds, the
        new value is set in `os.environ`.
        """
        await manager.update_secrets({"API_KEY": "old_value"})
        with open(dotenv_path, "w") as f:
            f.write('API_KEY="new_value"')
        await asyncio.sleep(3)
        assert os.environ["API_KEY"] == "new_value"
    

class TestEnvSecretsManagerWithInitialEnv():
    """
    Unit tests for the `EnvSecretsManager` in the special scenario where secrets
    are set in `os.environ` prior to each test.
    """
    # TODO
    pass
