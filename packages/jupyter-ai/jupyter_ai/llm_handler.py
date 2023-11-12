from typing import Dict, Type

from jupyter_ai.config_manager import ConfigManager, Logger
from jupyter_ai_magics.providers import BaseProvider


class BaseLLMHandler:
    """Base class containing shared methods and attributes used by LLM handler classes."""

    def __init__(
        self,
        log: Logger,
        config_manager: ConfigManager,
        model_parameters: Dict[str, Dict],
    ):
        self.log = log
        self.config_manager = config_manager
        self.model_parameters = model_parameters
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
                f"Switching chat language model from {curr_lm_id} to {next_lm_id}."
            )
            self.create_llm_chain(lm_provider, lm_provider_params)
            self.model_changed_callback()
        elif self.llm_params != lm_provider_params:
            self.log.info("Chat model params changed, updating the llm chain.")
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
