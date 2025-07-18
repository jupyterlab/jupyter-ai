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
    help = (
        "To use Vertex AI Generative AI you must have the langchain-google-vertexai Python package installed and either:\n\n"
        "- Have credentials configured for your environment (gcloud, workload identity, etc...)\n"
        "- Store the path to a service account JSON file as the GOOGLE_APPLICATION_CREDENTIALS environment variable\n\n"
        "This codebase uses the google.auth library which first looks for the application credentials variable mentioned above, and then looks for system-level auth. "
        "For more information, see the [Vertex AI authentication documentation](https://python.langchain.com/docs/integrations/llms/google_vertex_ai_palm/)."
    )

class VertexAIEmbeddingsProvider(BaseProvider, VertexAIEmbeddings):
    id = "vertexai"
    name = "Vertex AI"
    models = [
        "text-embedding-004",
    ]
    model_id_key = "model"
    auth_strategy = None
    pypi_package_deps = ["langchain-google-vertexai"]
    help = (
        "To use Vertex AI Generative AI you must have the langchain-google-vertexai Python package installed and either:\n\n"
        "- Have credentials configured for your environment (gcloud, workload identity, etc...)\n"
        "- Store the path to a service account JSON file as the GOOGLE_APPLICATION_CREDENTIALS environment variable\n\n"
        "This codebase uses the google.auth library which first looks for the application credentials variable mentioned above, and then looks for system-level auth. "
        "For more information, see the [Vertex AI authentication documentation](https://python.langchain.com/docs/integrations/llms/google_vertex_ai_palm/)."
    )