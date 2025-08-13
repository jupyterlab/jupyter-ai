"""
REST API endpoint for model parameter definitions.
"""
from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from tornado.web import authenticated, HTTPError
from pydantic import BaseModel
from typing import List, Optional

from litellm.litellm_core_utils.get_supported_openai_params import get_supported_openai_params

class ModelParametersResponse(BaseModel):
    """Response model for model parameters API."""
    #parameters: List[]
    count: int
    
class ModelParametersRestAPI(BaseAPIHandler):
    """
    REST API for model parameters at `/api/ai/model-parameters`
    
    GET /api/ai/model-parameters: Returns all supported OpenAI parameters
    GET /api/ai/model-parameters?core=true: Returns only core parameters
    """
    
    @authenticated
    def get(self):
        """
        Returns list of supported model parameters for OpenAI-compatible models.
        
        Query Parameters:
        - core (boolean): If true, returns only core/common parameters
        
        These parameters work with LiteLLM across different providers.
        """
        try:
            core_only = self.get_query_argument("core", default="false").lower() == "true"
            if core_only:
                parameters = get_core_parameters()
            else:
                parameters = get_supported_openai_params()
            
            response = ModelParametersResponse(
                parameters=parameters,
                count=len(parameters)
            )
            
            self.set_status(200)
            self.set_header("Content-Type", "application/json")
            self.finish(response.model_dump_json())
            
        except Exception as e:
            self.log.exception("Failed to get model parameters")
            raise HTTPError(500, f"Internal server error: {str(e)}")