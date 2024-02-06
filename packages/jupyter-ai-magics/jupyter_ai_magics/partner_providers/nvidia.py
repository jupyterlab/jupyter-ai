from jupyter_ai_magics.providers import BaseProvider, EnvAuthStrategy
from langchain_nvidia_ai_endpoints import ChatNVIDIA


class ChatNVIDIAProvider(BaseProvider, ChatNVIDIA):
    id = "nvidia-chat"
    name = "NVIDIA"
    models = [
        "playground_llama2_70b",
        "playground_nemotron_steerlm_8b",
        "playground_mistral_7b",
        "playground_nv_llama2_rlhf_70b",
        "playground_llama2_13b",
        "playground_steerlm_llama_70b",
        "playground_llama2_code_13b",
        "playground_yi_34b",
        "playground_mixtral_8x7b",
        "playground_neva_22b",
        "playground_llama2_code_34b",
    ]
    model_id_key = "model"
    auth_strategy = EnvAuthStrategy(name="NVIDIA_API_KEY")
    pypi_package_deps = ["langchain_nvidia_ai_endpoints"]
