from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from tornado.web import authenticated, HTTPError
import json

from litellm.litellm_core_utils.get_supported_openai_params import get_supported_openai_params
from .parameter_schemas import get_parameters_with_schemas
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
        - model (string): Model ID to get parameters for
        - provider (string): Custom LLM provider (optional)
        If no model provided, returns common parameters.
        """
        try:
            model = self.get_query_argument("model", default=None)
            provider = self.get_query_argument("provider", default=None)
            
            # Temporary common parameters that work across most models
            common_params = ["temperature", "max_tokens", "top_p", "stop"]
            
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
            
            # Get parameter schemas with types, defaults, and descriptions
            parameters_with_schemas = get_parameters_with_schemas(parameter_names)
            
            response = {
                "parameters": parameters_with_schemas,
                "parameter_names": parameter_names,
                "count": len(parameter_names)
            }
            
            self.set_status(200)
            self.set_header("Content-Type", "application/json")
            self.finish(json.dumps(response))
            
        except Exception as e:
            self.log.exception("Failed to get model parameters")
            raise HTTPError(500, f"Internal server error: {str(e)}")

    @authenticated
    def put(self):
        """
        Saves model parameters to configuration.
        Request body:
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
            model_id = request_body["model_id"]
            parameters = request_body["parameters"]
            
            config_manager = self.settings.get("jai_config_manager")
            if not config_manager:
                raise HTTPError(500, "Config manager not available")
            
            # Create update request with the parameters stored in fields
            update_request = UpdateConfigRequest(
                fields={model_id: parameters}
            )
            config_manager.update_config(update_request)
            
            response = {
                "status": "success",
                "message": f"Parameters saved for model {model_id}",
                "model_id": model_id,
                "parameters": parameters
            }
            
            self.set_status(200)
            self.set_header("Content-Type", "application/json")
            self.finish(json.dumps(response))
            
        except json.JSONDecodeError:
            raise HTTPError(400, "Invalid JSON in request body")
        except Exception as e:
            self.log.exception("Failed to save model parameters")
            raise HTTPError(500, f"Internal server error: {str(e)}")