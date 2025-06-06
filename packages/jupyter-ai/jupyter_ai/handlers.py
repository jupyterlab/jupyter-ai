from typing import TYPE_CHECKING, Optional, cast

from jupyter_ai.config_manager import ConfigManager, KeyEmptyError, WriteConflictError
from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from pydantic import ValidationError
from tornado import web
from tornado.web import HTTPError

from .models import (
    ListProvidersEntry,
    ListProvidersResponse,
    UpdateConfigRequest,
)

if TYPE_CHECKING:
    from jupyter_ai_magics.embedding_providers import BaseEmbeddingsProvider
    from jupyter_ai_magics.providers import BaseProvider


class ProviderHandler(BaseAPIHandler):
    """
    Helper base class used for HTTP handlers hosting endpoints relating to
    providers. Wrapper around BaseAPIHandler.
    """

    @property
    def lm_providers(self) -> dict[str, "BaseProvider"]:
        return self.settings["lm_providers"]

    @property
    def em_providers(self) -> dict[str, "BaseEmbeddingsProvider"]:
        return self.settings["em_providers"]

    @property
    def allowed_models(self) -> Optional[list[str]]:
        return self.settings["allowed_models"]

    @property
    def blocked_models(self) -> Optional[list[str]]:
        return self.settings["blocked_models"]

    def _filter_blocked_models(self, providers: list[ListProvidersEntry]):
        """
        Satisfy the model-level allow/blocklist by filtering models accordingly.
        The provider-level allow/blocklist is already handled in
        `AiExtension.initialize_settings()`.
        """
        if self.blocked_models is None and self.allowed_models is None:
            return providers

        def filter_predicate(local_model_id: str):
            model_id = provider.id + ":" + local_model_id
            if self.blocked_models:
                return model_id not in self.blocked_models
            else:
                return model_id in cast(list, self.allowed_models)

        # filter out every model w/ model ID according to allow/blocklist
        for provider in providers:
            provider.models = list(filter(filter_predicate, provider.models or []))
            provider.chat_models = list(
                filter(filter_predicate, provider.chat_models or [])
            )
            provider.completion_models = list(
                filter(filter_predicate, provider.completion_models or [])
            )

        # filter out every provider with no models which satisfy the allow/blocklist, then return
        return filter((lambda p: len(p.models) > 0), providers)


class ModelProviderHandler(ProviderHandler):
    @web.authenticated
    def get(self):
        providers = []

        # Step 1: gather providers
        for provider in self.lm_providers.values():
            optionals = {}
            if provider.model_id_label:
                optionals["model_id_label"] = provider.model_id_label

            providers.append(
                ListProvidersEntry(
                    id=provider.id,
                    name=provider.name,
                    models=provider.models,
                    chat_models=provider.chat_models(),
                    completion_models=provider.completion_models(),
                    help=provider.help,
                    auth_strategy=provider.auth_strategy,
                    registry=provider.registry,
                    fields=provider.fields,
                    **optionals,
                )
            )

        # Step 2: sort & filter providers
        providers = self._filter_blocked_models(providers)
        providers = sorted(providers, key=lambda p: p.name)

        # Finally, yield response.
        response = ListProvidersResponse(providers=providers)
        self.finish(response.model_dump_json())


class EmbeddingsModelProviderHandler(ProviderHandler):
    @web.authenticated
    def get(self):
        providers = []
        for provider in self.em_providers.values():
            providers.append(
                ListProvidersEntry(
                    id=provider.id,
                    name=provider.name,
                    models=provider.models,
                    help=provider.help,
                    auth_strategy=provider.auth_strategy,
                    registry=provider.registry,
                    fields=provider.fields,
                )
            )

        providers = self._filter_blocked_models(providers)
        providers = sorted(providers, key=lambda p: p.name)

        response = ListProvidersResponse(providers=providers)
        self.finish(response.model_dump_json())


class GlobalConfigHandler(BaseAPIHandler):
    """API handler for fetching and setting the
    model and emebddings config.
    """

    @property
    def config_manager(self):
        return self.settings["jai_config_manager"]

    @web.authenticated
    def get(self):
        config = self.config_manager.get_config()
        if not config:
            raise HTTPError(500, "No config found.")

        self.finish(config.model_dump_json())

    @web.authenticated
    def post(self):
        try:
            config = UpdateConfigRequest(**self.get_json_body())
            self.config_manager.update_config(config)
            self.set_status(204)
            self.finish()
        except (ValidationError, WriteConflictError, KeyEmptyError) as e:
            self.log.exception(e)
            raise HTTPError(500, str(e)) from e
        except ValueError as e:
            self.log.exception(e)
            raise HTTPError(500, str(e.cause) if hasattr(e, "cause") else str(e))
        except Exception as e:
            self.log.exception(e)
            raise HTTPError(
                500, "Unexpected error occurred while updating the config."
            ) from e


class ApiKeysHandler(BaseAPIHandler):
    @property
    def config_manager(self) -> ConfigManager:  # type:ignore[override]
        return self.settings["jai_config_manager"]

    @web.authenticated
    def delete(self, api_key_name: str):
        try:
            self.config_manager.delete_api_key(api_key_name)
        except Exception as e:
            raise HTTPError(500, str(e))


class InterruptStreamingHandler(BaseAPIHandler):
    """Interrupt a current message streaming"""

    @web.authenticated
    def post(self):
        message_id = self.get_json_body().get("message_id")
        message_interrupted = self.settings.get("jai_message_interrupted")
        if message_id and message_id in message_interrupted.keys():
            message_interrupted[message_id].set()
