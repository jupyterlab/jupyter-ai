import json
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from jsonschema import SchemaError, ValidationError
from jupyter_ai.mcp.mcp_config_loader import MCPConfigLoader


@pytest.fixture
def valid_config():
    """A valid MCP configuration for testing."""
    return {
        "mcpServers": {
            "test-server": {
                "command": "python",
                "args": ["test.py"],
                "env": {"TEST_VAR": "test_value"},
                "disabled": False,
            },
            "remote-server": {"url": "https://example.com/mcp", "transport": "http"},
        }
    }


@pytest.fixture
def invalid_config():
    """An invalid MCP configuration for testing."""
    return {"mcpServers": {"invalid-server": {"invalid_field": "should not be here"}}}


@pytest.fixture
def config_loader():
    """MCPConfigLoader instance for testing."""
    return MCPConfigLoader()


def test_mcp_config_loader_init(config_loader):
    """Test MCPConfigLoader initialization."""
    assert config_loader.schema is not None
    assert isinstance(config_loader.schema, dict)
    assert config_loader._cache == {}


def test_get_config_file_not_found(config_loader):
    """Test get_config when config file doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            config_loader.get_config(temp_dir)


def test_get_config_valid_file(config_loader, valid_config):
    """Test get_config with valid configuration file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mcp directory and config file
        mcp_dir = Path(temp_dir) / "mcp"
        mcp_dir.mkdir()
        config_file = mcp_dir / "config.json"

        with open(config_file, "w") as f:
            json.dump(valid_config, f)

        result = config_loader.get_config(temp_dir)
        assert result == valid_config


def test_get_config_invalid_json(config_loader):
    """Test get_config with malformed JSON."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mcp directory and invalid config file
        mcp_dir = Path(temp_dir) / "mcp"
        mcp_dir.mkdir()
        config_file = mcp_dir / "config.json"

        with open(config_file, "w") as f:
            f.write("{ invalid json }")

        with pytest.raises(json.JSONDecodeError, match="Invalid JSON in config file"):
            config_loader.get_config(temp_dir)


def test_get_config_validation_error(config_loader, invalid_config):
    """Test get_config with invalid configuration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mcp directory and invalid config file
        mcp_dir = Path(temp_dir) / "mcp"
        mcp_dir.mkdir()
        config_file = mcp_dir / "config.json"

        with open(config_file, "w") as f:
            json.dump(invalid_config, f)

        with pytest.raises(ValidationError, match="Configuration validation failed"):
            config_loader.get_config(temp_dir)


def test_get_config_caching(config_loader, valid_config):
    """Test that get_config caches configurations properly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mcp directory and config file
        mcp_dir = Path(temp_dir) / "mcp"
        mcp_dir.mkdir()
        config_file = mcp_dir / "config.json"

        with open(config_file, "w") as f:
            json.dump(valid_config, f)

        # First call should read from file
        result1 = config_loader.get_config(temp_dir)
        assert result1 == valid_config

        # Check cache was populated
        cache_info = config_loader.get_cache_info()
        assert cache_info["cached_files"] == 1
        assert str(config_file) in cache_info["cache_keys"]

        # Second call should use cache (mock file system to verify)
        with patch("builtins.open", mock_open()) as mock_file:
            result2 = config_loader.get_config(temp_dir)
            assert result2 == valid_config
            # File should not be opened for second call
            mock_file.assert_not_called()


def test_get_config_cache_invalidation(config_loader, valid_config):
    """Test that cache is invalidated when file is modified."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mcp directory and config file
        mcp_dir = Path(temp_dir) / "mcp"
        mcp_dir.mkdir()
        config_file = mcp_dir / "config.json"

        with open(config_file, "w") as f:
            json.dump(valid_config, f)

        # First call
        result1 = config_loader.get_config(temp_dir)
        assert result1 == valid_config

        # Modify the file
        modified_config = valid_config.copy()
        modified_config["mcpServers"]["new-server"] = {
            "command": "node",
            "args": ["server.js"],
        }

        # Sleep briefly to ensure different modification time
        import time

        time.sleep(0.01)

        with open(config_file, "w") as f:
            json.dump(modified_config, f)

        # Second call should read new content
        result2 = config_loader.get_config(temp_dir)
        assert result2 == modified_config
        assert result2 != result1


def test_validate_config_valid(config_loader, valid_config):
    """Test validate_config with valid configuration."""
    result = config_loader.validate_config(valid_config)
    assert result is True


def test_validate_config_invalid(config_loader, invalid_config):
    """Test validate_config with invalid configuration."""
    with pytest.raises(ValidationError):
        config_loader.validate_config(invalid_config)


def test_clear_cache(config_loader, valid_config):
    """Test clear_cache functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mcp directory and config file
        mcp_dir = Path(temp_dir) / "mcp"
        mcp_dir.mkdir()
        config_file = mcp_dir / "config.json"

        with open(config_file, "w") as f:
            json.dump(valid_config, f)

        # Load config to populate cache
        config_loader.get_config(temp_dir)

        # Verify cache is populated
        cache_info = config_loader.get_cache_info()
        assert cache_info["cached_files"] == 1

        # Clear cache
        config_loader.clear_cache()

        # Verify cache is empty
        cache_info = config_loader.get_cache_info()
        assert cache_info["cached_files"] == 0
        assert cache_info["cache_keys"] == []


def test_get_cache_info(config_loader, valid_config):
    """Test get_cache_info functionality."""
    # Initially empty
    cache_info = config_loader.get_cache_info()
    assert cache_info["cached_files"] == 0
    assert cache_info["cache_keys"] == []

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mcp directory and config file
        mcp_dir = Path(temp_dir) / "mcp"
        mcp_dir.mkdir()
        config_file = mcp_dir / "config.json"

        with open(config_file, "w") as f:
            json.dump(valid_config, f)

        # Load config
        config_loader.get_config(temp_dir)

        # Check cache info
        cache_info = config_loader.get_cache_info()
        assert cache_info["cached_files"] == 1
        assert str(config_file) in cache_info["cache_keys"]


def test_schema_error_handling():
    """Test handling of schema errors during initialization."""
    with patch("builtins.open", mock_open(read_data="invalid json schema")):
        with pytest.raises(json.JSONDecodeError):
            MCPConfigLoader()


def test_multiple_configs_caching(config_loader, valid_config):
    """Test caching with multiple different config files."""
    with (
        tempfile.TemporaryDirectory() as temp_dir1,
        tempfile.TemporaryDirectory() as temp_dir2,
    ):

        # Create first config
        mcp_dir1 = Path(temp_dir1) / "mcp"
        mcp_dir1.mkdir()
        config_file1 = mcp_dir1 / "config.json"

        with open(config_file1, "w") as f:
            json.dump(valid_config, f)

        # Create second config
        mcp_dir2 = Path(temp_dir2) / "mcp"
        mcp_dir2.mkdir()
        config_file2 = mcp_dir2 / "config.json"

        config2 = {
            "mcpServers": {
                "different-server": {"command": "different", "args": ["different.py"]}
            }
        }

        with open(config_file2, "w") as f:
            json.dump(config2, f)

        # Load both configs
        result1 = config_loader.get_config(temp_dir1)
        result2 = config_loader.get_config(temp_dir2)

        assert result1 == valid_config
        assert result2 == config2

        # Check both are cached
        cache_info = config_loader.get_cache_info()
        assert cache_info["cached_files"] == 2
        assert str(config_file1) in cache_info["cache_keys"]
        assert str(config_file2) in cache_info["cache_keys"]


def test_config_with_minimal_server():
    """Test configuration with minimal required fields."""
    config_loader = MCPConfigLoader()
    minimal_config = {
        "mcpServers": {
            "minimal-local": {"command": "python", "args": ["server.py"]},
            "minimal-remote": {"url": "https://example.com/mcp"},
        }
    }

    # This should validate successfully
    assert config_loader.validate_config(minimal_config) is True


def test_config_with_all_optional_fields():
    """Test configuration with all optional fields."""
    config_loader = MCPConfigLoader()
    full_config = {
        "mcpServers": {
            "full-server": {
                "command": "python",
                "args": ["server.py", "--verbose"],
                "env": {"DEBUG": "true", "LOG_LEVEL": "info"},
                "disabled": True,
                "transport": "stdio",
            }
        }
    }

    # This should validate successfully
    assert config_loader.validate_config(full_config) is True
