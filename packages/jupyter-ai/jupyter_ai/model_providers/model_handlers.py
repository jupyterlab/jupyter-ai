from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from pydantic import BaseModel
from tornado import web

from .model_list import CHAT_MODELS


class ChatModelEndpoint(BaseAPIHandler):
    """
    A handler class that defines the `/api/ai/models/chat` endpoint.

    - `GET /api/ai/models/chat`: returns list of all chat models.

    - `GET /api/ai/models/chat?id=<model_id>`: returns info on that model (TODO)
    """

    @web.authenticated
    def get(self):
        response = ListChatModelsResponse(chat_models=CHAT_MODELS)
        self.finish(response.model_dump_json())


class ListChatModelsResponse(BaseModel):
    chat_models: list[str]


class ListEmbeddingModelsResponse(BaseModel):
    embedding_models: list[str]
