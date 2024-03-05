from jupyter_ai_magics.providers import BaseProvider, EnvAuthStrategy
from langchain_google_genai import GoogleGenerativeAI


class GeminiProvider(BaseProvider, GoogleGenerativeAI):
    id = "gemini"
    name = "Gemini"
    models = [
        "gemini-pro",
    ]
    model_id_key = "model"
    auth_strategy = EnvAuthStrategy(name="GOOGLE_API_KEY")
    pypi_package_deps = ["langchain-google-genai"]
