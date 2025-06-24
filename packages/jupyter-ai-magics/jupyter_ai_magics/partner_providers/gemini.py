from jupyter_ai_magics.base_provider import BaseProvider, EnvAuthStrategy
from langchain_google_genai import GoogleGenerativeAI


# See list of model ids here: https://ai.google.dev/gemini-api/docs/models/gemini
class GeminiProvider(BaseProvider, GoogleGenerativeAI):
    id = "gemini"
    name = "Gemini"
    models = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]
    model_id_key = "model"
    auth_strategy = EnvAuthStrategy(name="GOOGLE_API_KEY")
    pypi_package_deps = ["langchain-google-genai"]
