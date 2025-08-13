from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from tornado.web import authenticated, HTTPError
import json

from litellm.litellm_core_utils.get_supported_openai_params import get_supported_openai_params
    
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
                    parameters = get_supported_openai_params(
                        model=model,
                        custom_llm_provider=provider
                    )
                    if not parameters:
                        parameters = common_params
                except Exception:
                    parameters = common_params
            else:
                parameters = common_params
            
            response = {
                "parameters": parameters,
                "count": len(parameters)
            }
            
            self.set_status(200)
            self.set_header("Content-Type", "application/json")
            self.finish(json.dumps(response))
            
        except Exception as e:
            self.log.exception("Failed to get model parameters")
            raise HTTPError(500, f"Internal server error: {str(e)}")