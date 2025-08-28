from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from tornado.web import authenticated, HTTPError
import json

from litellm.litellm_core_utils.get_supported_openai_params import get_supported_openai_params
from .parameter_schemas import get_parameters_with_schemas, coerce_parameter_value, GetModelParametersResponse, UpdateModelParametersResponse
from ..config_manager import ConfigManager
from ..config import UpdateConfigRequest
    
class ModelParametersRestAPI(BaseAPIHandler):
    """
    REST API for model parameters at `/api/ai/model-parameters`
    
    GET /api/ai/model-parameters: Returns common parameters
    GET /api/ai/model-parameters?model=gpt-4: Returns parameters for specific model
    PUT /api/ai/model-parameters: Saves model parameters to config
    """
    
    @authenticated
    def get(self):
        """
        Returns list of supported model parameters.
        
        Query Parameters:
        - model (string, optional): Model ID to get parameters for
        - provider (string, optional): Custom LLM provider
        If no model provided, returns common parameters.
        """
        try:
            model = self.get_query_argument("model", default=None)
            provider = self.get_query_argument("provider", default=None)
            
            # Temporary common parameters that work across most models
            common_params = ["temperature", "max_tokens", "top_p", "stop"]
            # Params controlling tool availability & usage require a unique UX
            # if they are to be made configurable from the frontend. Therefore
            # they are disabled for now.
            EXCLUDED_PARAMS = { "tools", "tool_choice", "parallel_tool_calls" }
            
            if model:
                try:
                    parameter_names = get_supported_openai_params(
                        model=model,
                        custom_llm_provider=provider
                    )
                    if not parameter_names:
                        parameter_names = common_params
                except Exception:
                    parameter_names = common_params
            else:
                parameter_names = common_params
            
            # Filter out excluded params
            parameter_names = [n for n in parameter_names if n not in EXCLUDED_PARAMS]
            
            # Get parameter schemas with types, defaults, and descriptions
            parameters_with_schemas = get_parameters_with_schemas(parameter_names)
            
            # Create Pydantic response model
            response = GetModelParametersResponse(
                parameters=parameters_with_schemas,
                parameter_names=parameter_names
            )
            
            self.set_header("Content-Type", "application/json")
            self.finish(response.model_dump_json())
            
        except Exception as e:
            self.log.exception("Failed to get model parameters")
            raise HTTPError(500, f"Internal server error: {str(e)}")

    @authenticated
    def put(self):
        """
        Saves model parameters to configuration.
        Example request body:
        {
            "model_id": "gpt-4", 
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
        """
        try:
            request_body = json.loads(self.request.body.decode('utf-8'))
            
            # Validate required fields
            if "model_id" not in request_body:
                raise HTTPError(400, "Missing required field: model_id")
            if "parameters" not in request_body:
                raise HTTPError(400, "Missing required field: parameters")
                
            model_id = request_body["model_id"]
            parameters = request_body["parameters"]
            
            # Validate parameter structure and apply type coercion
            coerced_parameters = {}
            for param_name, param_data in parameters.items():
                if not isinstance(param_data, dict):
                    raise HTTPError(400, f"Parameter '{param_name}' must be an object with 'value' and 'type' fields")
                if "value" not in param_data:
                    raise HTTPError(400, f"Parameter '{param_name}' missing required field: value")
                if "type" not in param_data:
                    raise HTTPError(400, f"Parameter '{param_name}' missing required field: type")
                try:
                    coerced_value = coerce_parameter_value(param_data["value"], param_data["type"])
                    coerced_parameters[param_name] = coerced_value
                except ValueError as e:
                    raise HTTPError(400, f"Invalid value for parameter '{param_name}': {str(e)}")
            
            config_manager = self.settings.get("jai_config_manager")
            if not config_manager:
                raise HTTPError(500, "Config manager not available")
            
            update_request = UpdateConfigRequest(
                fields={model_id: coerced_parameters}
            )
            config_manager.update_config(update_request)
            
            # Create Pydantic response model for API compatibility
            response = UpdateModelParametersResponse(
                status="success",
                message=f"Parameters saved for model {model_id}",
                model_id=model_id,
                parameters=coerced_parameters
            )
            
            self.set_header("Content-Type", "application/json")
            self.finish(response.model_dump_json())
            
        except json.JSONDecodeError:
            raise HTTPError(400, "Invalid JSON in request body")
        except Exception as e:
            self.log.exception("Failed to save model parameters")
            raise HTTPError(500, f"Internal server error: {str(e)}")
