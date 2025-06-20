import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError
from jsonschema.exceptions import SchemaError

class MCPConfigLoader:
    """Loader for MCP server configuration files with JSON schema validation."""
    
    def __init__(self):
        # Load the schema from the schema.json file
        schema_path = Path(__file__).parent / "schema.json"
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)
    
    def get_config(self, config_path: str) -> Dict[str, Any]:
        """
        Read and validate an MCP server configuration file.
        
        Args:
            config_path (str): Path to the JSON configuration file
            
        Returns:
            Dict[str, Any]: The validated configuration object
            
        Raises:
            FileNotFoundError: If the config file doesn't exist
            json.JSONDecodeError: If the JSON is malformed
            ValidationError: If the config doesn't match the schema
            SchemaError: If there's an issue with the schema itself
        """
        config_path = Path(config_path)
        
        # Check if file exists
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Read the JSON file
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in config file {config_path}: {e.msg}", e.doc, e.pos)
        
        # Validate against schema
        try:
            validate(instance=config, schema=self.schema)
        except ValidationError as e:
            raise ValidationError(f"Configuration validation failed: {e.message}")
        except SchemaError as e:
            raise SchemaError(f"Schema error: {e.message}")
        
        return config
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate a configuration object against the schema.
        
        Args:
            config (Dict[str, Any]): Configuration object to validate
            
        Returns:
            bool: True if valid, raises exception if invalid
        """
        validate(instance=config, schema=self.schema)
        return True
