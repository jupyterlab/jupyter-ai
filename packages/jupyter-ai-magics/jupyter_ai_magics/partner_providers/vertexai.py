from jupyter_ai_magics.base_provider import BaseProvider
from langchain_google_vertexai import VertexAI, VertexAIEmbeddings


class VertexAIProvider(BaseProvider, VertexAI):
    id = "vertexai"
    name = "Vertex AI"
    models = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
    ]
    model_id_key = "model"
    auth_strategy = None
    pypi_package_deps = ["langchain-google-vertexai"]

class VertexAIEmbeddingsProvider(BaseProvider, VertexAIEmbeddings):
    id = "vertexai"
    name = "Vertex AI"
    models = [
        "text-embedding-004",
    ]
    model_id_key = "model"
    auth_strategy = None
    pypi_package_deps = ["langchain-google-vertexai"]