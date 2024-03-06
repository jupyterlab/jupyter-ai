from jupyter_ai_magics.providers import BaseProvider, EnvAuthStrategy
from langchain_google_genai import GoogleGenerativeAI


class GeminiProvider(BaseProvider, GoogleGenerativeAI):
    id = "gemini"
    name = "Gemini"
    models = [
        "gemini-1.0-pro",
        "gemini-1.0-pro-001",
        "gemini-1.0-pro-latest",
        "gemini-1.0-pro-vision-latest",
        "gemini-pro",
        "gemini-pro-vision",
    ]
    model_id_key = "model"
    auth_strategy = EnvAuthStrategy(name="GOOGLE_API_KEY")
    pypi_package_deps = ["langchain-google-genai"]
