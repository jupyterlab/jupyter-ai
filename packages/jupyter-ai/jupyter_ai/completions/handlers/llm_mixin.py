from typing import Any, Dict, Type

from jupyter_ai.config_manager import ConfigManager
from jupyter_ai_magics.providers import BaseProvider


class LLMHandlerMixin:
    """Base class containing shared methods and attributes used by LLM handler classes."""

    # This could be used to derive `BaseChatHandler` too (there is a lot of duplication!),
    # but it was decided against it to avoid introducing conflicts for backports against 1.x

    handler_kind: str

    @property
    def config_manager(self) -> ConfigManager:
        return self.settings["jai_config_manager"]

    @property
    def model_parameters(self) -> Dict[str, Dict[str, Any]]:
        return self.settings["model_parameters"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = None
        self.llm_params = None
        self.llm_chain = None

    def get_llm_chain(self):
        lm_provider = self.config_manager.lm_provider
        lm_provider_params = self.config_manager.lm_provider_params

        curr_lm_id = (
            f'{self.llm.id}:{lm_provider_params["model_id"]}' if self.llm else None
        )
        next_lm_id = (
            f'{lm_provider.id}:{lm_provider_params["model_id"]}'
            if lm_provider
            else None
        )

        if not lm_provider or not lm_provider_params:
            return None

        if curr_lm_id != next_lm_id:
            self.log.info(
                f"Switching {self.handler_kind} language model from {curr_lm_id} to {next_lm_id}."
            )
            self.create_llm_chain(lm_provider, lm_provider_params)
        elif self.llm_params != lm_provider_params:
            self.log.info(
                f"{self.handler_kind} model params changed, updating the llm chain."
            )
            self.create_llm_chain(lm_provider, lm_provider_params)

        self.llm_params = lm_provider_params
        return self.llm_chain

    def get_model_parameters(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        return self.model_parameters.get(
            f"{provider.id}:{provider_params['model_id']}", {}
        )

    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        raise NotImplementedError("Should be implemented by subclasses")
