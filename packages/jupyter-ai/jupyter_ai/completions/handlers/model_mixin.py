from logging import Logger
from typing import Any, Dict, Optional, Type

from jupyter_ai.config_manager import ConfigManager
from jupyter_ai_magics.providers import BaseProvider


class CompletionsModelMixin:
    """Mixin class containing methods and attributes used by completions LLM handler."""

    handler_kind: str
    settings: dict
    log: Logger

    @property
    def jai_config_manager(self) -> ConfigManager:
        return self.settings["jai_config_manager"]

    @property
    def model_parameters(self) -> Dict[str, Dict[str, Any]]:
        return self.settings["model_parameters"]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._llm: Optional[BaseProvider] = None
        self._llm_params = None

    def get_llm(self) -> Optional[BaseProvider]:
        lm_provider = self.jai_config_manager.completions_lm_provider
        lm_provider_params = self.jai_config_manager.completions_lm_provider_params

        if not lm_provider or not lm_provider_params:
            return None

        curr_lm_id = (
            f'{self._llm.id}:{lm_provider_params["model_id"]}' if self._llm else None
        )
        next_lm_id = (
            f'{lm_provider.id}:{lm_provider_params["model_id"]}'
            if lm_provider
            else None
        )

        should_recreate_llm = False
        if curr_lm_id != next_lm_id:
            self.log.info(
                f"Switching {self.handler_kind} language model from {curr_lm_id} to {next_lm_id}."
            )
            should_recreate_llm = True
        elif self._llm_params != lm_provider_params:
            self.log.info(
                f"{self.handler_kind} model params changed, updating the llm chain."
            )
            should_recreate_llm = True

        if should_recreate_llm:
            self._llm = self.create_llm(lm_provider, lm_provider_params)
            self._llm_params = lm_provider_params

        return self._llm

    def get_model_parameters(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        return self.model_parameters.get(
            f"{provider.id}:{provider_params['model_id']}", {}
        )

    def create_llm(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ) -> BaseProvider:
        unified_parameters = {
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        llm = provider(**unified_parameters)

        return llm
