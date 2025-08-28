from __future__ import annotations
from typing import TYPE_CHECKING, cast, Literal, Optional
from pydantic import BaseModel

if TYPE_CHECKING:
    from typing import Any


PARAMETER_SCHEMAS: dict[str, dict[str, Any]] = {
    "temperature": {
        "type": "float",
        "min": 0,
        "max": 2,
        "description": "Controls randomness in the output. Lower values make it more focused and deterministic."
    },
    "top_p": {
        "type": "float", 
        "min": 0,
        "max": 1,
        "description": "Nucleus sampling parameter. Consider tokens with top_p probability mass."
    },
    "max_tokens": {
        "type": "integer",
        "min": 1,
        "description": "The maximum number of tokens to generate in the completion."
    },
    "max_completion_tokens": {
        "type": "integer",
        "min": 1,
        "description": "Upper bound for the number of tokens that can be generated for a completion."
    },
    "n": {
        "type": "integer",
        "min": 1,
        "max": 128,
        "description": "How many completion choices to generate for each prompt."
    },
    "seed": {
        "type": "integer",
        "description": "Seed for deterministic sampling. Same seed and parameters should return same result."
    },
    "stream": {
        "type": "boolean",
        "description": "Whether to stream partial message deltas."
    },
    "stop": {
        "type": "array",
        "description": "Up to 4 sequences where the API will stop generating further tokens."
    },
    "response_format": {
        "type": "object",
        "description": "Specify the format that the model must output (e.g., JSON)."
    },
    
    # Model Behavior  
    # "tools": {
    #     "type": "array",
    #     "default": None,
    #     "description": "A list of tools the model may call."
    # },
    # "tool_choice": {
    #     "type": "string|object",
    #     "default": "auto",
    #     "description": "Controls which function is called by the model."
    # },
    # "parallel_tool_calls": {
    #     "type": "boolean",
    #     "default": True,
    #     "description": "Whether to enable parallel function calling during tool use."
    # },
    
    "presence_penalty": {
        "type": "float",
        "min": -2,
        "max": 2,
        "description": "Penalize new tokens based on whether they appear in the text so far."
    },
    "frequency_penalty": {
        "type": "float",
        "min": -2,
        "max": 2,
        "description": "Penalize new tokens based on their frequency in the text so far."
    },
    "logit_bias": {
        "type": "object",
        "description": "Modify the likelihood of specified tokens appearing in the completion."
    },
    "logprobs": {
        "type": "boolean",
        "description": "Whether to return log probabilities of the output tokens."
    },
    "top_logprobs": {
        "type": "integer",
        "min": 0,
        "max": 5,
        "description": "Number of most likely tokens to return at each token position."
    },
    "user": {
        "type": "string",
        "description": "A unique identifier representing your end-user."
    },
    "timeout": {
        "type": "integer",
        "min": 1,
        "description": "Request timeout in seconds."
    },
    "top_k": {
        "type": "integer",
        "min": 1,
        "description": "Limit the next token selection to the K most probable tokens."
    }
}


class ParameterSchema(BaseModel):
    """Pydantic model for parameter schema definition."""
    type: Literal['boolean', 'integer', 'float', 'string', 'array', 'object']
    description: str
    min: Optional[float] = None
    max: Optional[float] = None


class GetModelParametersResponse(BaseModel):
    """Pydantic model for GET model parameters response."""
    parameters: dict[str, ParameterSchema]
    parameter_names: list[str]


def get_parameter_schema(param_name: str) -> ParameterSchema:
    """
    Get the schema for a specific parameter.
    """
    schema = PARAMETER_SCHEMAS.get(param_name)
    if schema is None:
        return ParameterSchema(
            type="string",
            description=f"Parameter {param_name} (schema not defined)"
        )
    return ParameterSchema(**schema)

def get_parameters_with_schemas(param_names: list[str]) -> dict[str, ParameterSchema]:
    """
    Get schemas for a list of parameter names.
    """
    return {
        name: get_parameter_schema(name) 
        for name in param_names
    }

def coerce_parameter_value(value: str, param_type: str):
    """
    Coerce a string value to the appropriate type based on parameter type.
    
    Args:
        value: The string value to coerce
        param_type: The parameter type (e.g., 'number', 'integer', 'boolean', 'string')
    
    Returns:
        The coerced value in the appropriate type
        
    Raises:
        ValueError: If the value cannot be coerced to the specified type
    """
    if not isinstance(value, str):
        return value  # Already the correct type
    
    # Normalize the type string
    param_type = param_type.lower().strip()
    
    # Handle different types
    if param_type in ['number', 'float']:
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Cannot convert '{value}' to number")
            
    elif param_type in ['integer', 'int']:
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Cannot convert '{value}' to integer")
            
    elif param_type in ['boolean', 'bool']:
        value_lower = value.lower().strip()
        if value_lower == 'true':
            return True
        elif value_lower == 'false':
            return False
        else:
            raise ValueError(f"Cannot convert '{value}' to boolean (expected 'true' or 'false')")
            
    elif param_type in ['string', 'str']:
        return value  # Already a string
        
    elif param_type in ['array', 'list']:
        try:
            import json
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            raise ValueError(f"Cannot convert '{value}' to array (expected valid JSON array)")
            
    elif param_type in ['object', 'dict']:
        try:
            import json
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            raise ValueError(f"Cannot convert '{value}' to object (expected valid JSON object)")
        
    else:
        # For unknown types, return as string
        return value