from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from tornado.web import authenticated, HTTPError
import json

from litellm.litellm_core_utils.get_supported_openai_params import get_supported_openai_params
from .parameter_schemas import get_parameters_with_schemas
    
class ModelParametersRestAPI(BaseAPIHandler):
    """
    REST API for model parameters at `/api/ai/model-parameters`
    
    GET /api/ai/model-parameters: Returns common parameters
    GET /api/ai/model-parameters?model=gpt-4: Returns parameters for specific model
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