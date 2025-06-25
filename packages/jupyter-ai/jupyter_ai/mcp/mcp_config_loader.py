import json
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate
from jsonschema.exceptions import SchemaError

SCHEMA_FILE = Path(__file__).parent / "schema.json"


class MCPConfigLoader:
    """Loader for MCP server configuration files with JSON schema validation."""

    def __init__(self):
        # Load the schema from the schema.json file
        with open(SCHEMA_FILE) as f:
            self.schema = json.load(f)

        # Cache for storing configurations and their modification times
        # Key: config_path (str), Value: (config_dict, last_modified_time)
        self._cache: dict[str, tuple[dict[str, Any], float]] = {}

    def get_config(self, jupyter_dir: str) -> dict[str, Any]:
        """
        Read and validate an MCP server configuration file from .jupyter/mcp/config.json.

        Args:
            jupyter_dir (str): Path to the .jupyter directory

        Returns:
            Dict[str, Any]: The validated configuration object

        Raises:
            FileNotFoundError: If the config file doesn't exist
            json.JSONDecodeError: If the JSON is malformed
            ValidationError: If the config doesn't match the schema
            SchemaError: If there's an issue with the schema itself
        """
        config_path = Path(jupyter_dir) / "mcp" / "config.json"
        config_path_str = str(config_path)

        # Check if file exists
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Get current file modification time
        current_mtime = config_path.stat().st_mtime

        # Check cache first
        if config_path_str in self._cache:
            cached_config, cached_mtime = self._cache[config_path_str]

            # If file hasn't been modified, return cached version
            if current_mtime == cached_mtime:
                return cached_config

        # File is new or has been modified, read and validate it
        try:
            with open(config_path) as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in config file {config_path}: {e.msg}", e.doc, e.pos
            )

        # Validate against schema
        try:
            validate(instance=config, schema=self.schema)
        except ValidationError as e:
            raise ValidationError(f"Configuration validation failed: {e.message}")
        except SchemaError as e:
            raise SchemaError(f"Schema error: {e.message}")

        # Cache the validated configuration and its modification time
        self._cache[config_path_str] = (config, current_mtime)

        return config

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate a configuration object against the schema.

        Args:
            config (Dict[str, Any]): Configuration object to validate

        Returns:
            bool: True if valid, raises exception if invalid
        """
        validate(instance=config, schema=self.schema)
        return True

    def clear_cache(self) -> None:
        """
        Clear the configuration cache.
        """
        self._cache.clear()

    def get_cache_info(self) -> dict[str, Any]:
        """
        Get information about the cache.

        Returns:
            Dict[str, Any]: Dictionary with cache statistics
        """
        return {
            "cached_files": len(self._cache),
            "cache_keys": list(self._cache.keys()),
        }
