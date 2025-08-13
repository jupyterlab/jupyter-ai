
PARAMETER_SCHEMAS = {
    "temperature": {
        "type": "number",
        "default": 1,
        "min": 0,
        "max": 2,
        "description": "Controls randomness in the output. Lower values make it more focused and deterministic."
    },
    "top_p": {
        "type": "number", 
        "default": 1,
        "min": 0,
        "max": 1,
        "description": "Nucleus sampling parameter. Consider tokens with top_p probability mass."
    },
    "max_tokens": {
        "type": "integer",
        "default": None,
        "min": 1,
        "description": "The maximum number of tokens to generate in the completion."
    },
    "max_completion_tokens": {
        "type": "integer",
        "default": None,
        "min": 1,
        "description": "Upper bound for the number of tokens that can be generated for a completion."
    },
    "n": {
        "type": "integer",
        "default": 1,
        "min": 1,
        "max": 128,
        "description": "How many completion choices to generate for each prompt."
    },
    "seed": {
        "type": "integer",
        "default": None,
        "description": "Seed for deterministic sampling. Same seed and parameters should return same result."
    },
    
    # Response Formatting
    "stream": {
        "type": "boolean",
        "default": False,
        "description": "Whether to stream partial message deltas."
    },
    "stop": {
        "type": "array",
        "default": None,
        "description": "Up to 4 sequences where the API will stop generating further tokens."
    },
    "response_format": {
        "type": "object",
        "default": None,
        "description": "Specify the format that the model must output (e.g., JSON)."
    },
    
    # Model Behavior  
    "tools": {
        "type": "array",
        "default": None,
        "description": "A list of tools the model may call."
    },
    "tool_choice": {
        "type": "string|object",
        "default": "auto",
        "description": "Controls which function is called by the model."
    },
    "parallel_tool_calls": {
        "type": "boolean",
        "default": True,
        "description": "Whether to enable parallel function calling during tool use."
    },
    
    # Penalty/Bias Parameters
    "presence_penalty": {
        "type": "number",
        "default": 0,
        "min": -2,
        "max": 2,
        "description": "Penalize new tokens based on whether they appear in the text so far."
    },
    "frequency_penalty": {
        "type": "number",
        "default": 0,
        "min": -2,
        "max": 2,
        "description": "Penalize new tokens based on their frequency in the text so far."
    },
    "logit_bias": {
        "type": "object",
        "default": None,
        "description": "Modify the likelihood of specified tokens appearing in the completion."
    },
    
    # Logging/Debugging
    "logprobs": {
        "type": "boolean",
        "default": False,
        "description": "Whether to return log probabilities of the output tokens."
    },
    "top_logprobs": {
        "type": "integer",
        "default": None,
        "min": 0,
        "max": 5,
        "description": "Number of most likely tokens to return at each token position."
    },
    "user": {
        "type": "string",
        "default": None,
        "description": "A unique identifier representing your end-user."
    },
    
    # Additional Technical Parameters
    "timeout": {
        "type": "integer",
        "default": None,
        "min": 1,
        "description": "Request timeout in seconds."
    },
    "top_k": {
        "type": "integer",
        "default": None,
        "min": 1,
        "description": "Limit the next token selection to the K most probable tokens."
    }
}

def get_parameter_schema(param_name: str) -> dict:
    """Get schema for a specific parameter."""
    return PARAMETER_SCHEMAS.get(param_name, {
        "type": "string",
        "default": None,
        "description": f"Parameter {param_name} (schema not defined)"
    })

def get_parameters_with_schemas(param_names: list) -> dict:
    """Get schemas for a list of parameter names."""
    return {
        name: get_parameter_schema(name) 
        for name in param_names
    }