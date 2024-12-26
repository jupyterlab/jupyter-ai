from typing import TYPE_CHECKING, Dict, List, Optional, Type, cast

from jupyter_ai.chat_handlers import (
    AskChatHandler,
    DefaultChatHandler,
    GenerateChatHandler,
    HelpChatHandler,
    LearnChatHandler,
    SlashCommandRoutingType,
)
from jupyter_ai.config_manager import ConfigManager, KeyEmptyError, WriteConflictError
from jupyter_ai.context_providers import BaseCommandContextProvider, ContextCommand
from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from langchain.pydantic_v1 import ValidationError
from tornado import web
from tornado.web import HTTPError

from .models import (
    ListOptionsEntry,
    ListOptionsResponse,
    ListProvidersEntry,
    ListProvidersResponse,
    ListSlashCommandsEntry,
    ListSlashCommandsResponse,
    UpdateConfigRequest,
)

if TYPE_CHECKING:
    from jupyter_ai_magics.embedding_providers import BaseEmbeddingsProvider
    from jupyter_ai_magics.providers import BaseProvider

    from .chat_handlers import BaseChatHandler
    from .context_providers import BaseCommandContextProvider

# TODO v3: unify loading of chat handlers in a single place, then read
# from that instead of this hard-coded dict.
CHAT_HANDLER_DICT = {
    "default": DefaultChatHandler,
    "/ask": AskChatHandler,
    "/learn": LearnChatHandler,
    "/generate": GenerateChatHandler,
    "/help": HelpChatHandler,
}


class ProviderHandler(BaseAPIHandler):
    """
    Helper base class used for HTTP handlers hosting endpoints relating to
    providers. Wrapper around BaseAPIHandler.
    """

    @property
    def lm_providers(self) -> Dict[str, "BaseProvider"]:
        return self.settings["lm_providers"]

    @property
    def em_providers(self) -> Dict[str, "BaseEmbeddingsProvider"]:
        return self.settings["em_providers"]

    @property
    def allowed_models(self) -> Optional[List[str]]:
        return self.settings["allowed_models"]

    @property
    def blocked_models(self) -> Optional[List[str]]:
        return self.settings["blocked_models"]

    def _filter_blocked_models(self, providers: List[ListProvidersEntry]):
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
                return model_id in cast(List, self.allowed_models)

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
        self.finish(response.json())


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
                    auth_strategy=provider.auth_strategy,
                    registry=provider.registry,
                    fields=provider.fields,
                )
            )

        providers = self._filter_blocked_models(providers)
        providers = sorted(providers, key=lambda p: p.name)

        response = ListProvidersResponse(providers=providers)
        self.finish(response.json())


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

        self.finish(config.json())

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


class SlashCommandsInfoHandler(BaseAPIHandler):
    """List slash commands that are currently available to the user."""

    @property
    def config_manager(self) -> ConfigManager:  # type:ignore[override]
        return self.settings["jai_config_manager"]

    @property
    def chat_handlers(self) -> Dict[str, Type["BaseChatHandler"]]:
        return CHAT_HANDLER_DICT

    @web.authenticated
    def get(self):
        response = ListSlashCommandsResponse()

        # if no selected LLM, return an empty response
        if not self.config_manager.lm_provider:
            self.finish(response.json())
            return

        for id, chat_handler in self.chat_handlers.items():
            # filter out any chat handler that is not a slash command
            if (
                id == "default"
                or chat_handler.routing_type.routing_method != "slash_command"
            ):
                continue

            # hint the type of this attribute
            routing_type: SlashCommandRoutingType = chat_handler.routing_type

            # filter out any chat handler that is unsupported by the current LLM
            if (
                "/" + routing_type.slash_id
                in self.config_manager.lm_provider.unsupported_slash_commands
            ):
                continue

            response.slash_commands.append(
                ListSlashCommandsEntry(
                    slash_id=routing_type.slash_id, description=chat_handler.help
                )
            )

        # sort slash commands by slash id and deliver the response
        response.slash_commands.sort(key=lambda sc: sc.slash_id)
        self.finish(response.json())


class AutocompleteOptionsHandler(BaseAPIHandler):
    """List context that are currently available to the user."""

    @property
    def config_manager(self) -> ConfigManager:  # type:ignore[override]
        return self.settings["jai_config_manager"]

    @property
    def context_providers(self) -> Dict[str, "BaseCommandContextProvider"]:
        return self.settings["jai_context_providers"]

    @property
    def chat_handlers(self) -> Dict[str, Type["BaseChatHandler"]]:
        return CHAT_HANDLER_DICT

    @web.authenticated
    def get(self):
        response = ListOptionsResponse()

        # if no selected LLM, return an empty response
        if not self.config_manager.lm_provider:
            self.finish(response.json())
            return

        partial_cmd = self.get_query_argument("partialCommand", None)
        if partial_cmd:
            # if providing options for partial command argument
            cmd = ContextCommand(cmd=partial_cmd)
            context_provider = next(
                (
                    cp
                    for cp in self.context_providers.values()
                    if isinstance(cp, BaseCommandContextProvider)
                    and cp.command_id == cmd.id
                ),
                None,
            )
            if (
                cmd.arg is not None
                and context_provider
                and isinstance(context_provider, BaseCommandContextProvider)
            ):
                response.options = context_provider.get_arg_options(cmd.arg)
        else:
            response.options = (
                self._get_slash_command_options() + self._get_context_provider_options()
            )
        self.finish(response.json())

    def _get_slash_command_options(self) -> List[ListOptionsEntry]:
        options = []
        for id, chat_handler in self.chat_handlers.items():
            # filter out any chat handler that is not a slash command
            if id == "default" or not isinstance(
                chat_handler.routing_type, SlashCommandRoutingType
            ):
                continue

            routing_type = chat_handler.routing_type

            # filter out any chat handler that is unsupported by the current LLM
            if (
                not routing_type.slash_id
                or "/" + routing_type.slash_id
                in self.config_manager.lm_provider.unsupported_slash_commands
            ):
                continue

            options.append(
                self._make_autocomplete_option(
                    id="/" + routing_type.slash_id,
                    description=chat_handler.help,
                    only_start=True,
                    requires_arg=False,
                )
            )
        options.sort(key=lambda opt: opt.id)
        return options

    def _get_context_provider_options(self) -> List[ListOptionsEntry]:
        options = [
            self._make_autocomplete_option(
                id=context_provider.command_id,
                description=context_provider.help,
                only_start=context_provider.only_start,
                requires_arg=context_provider.requires_arg,
            )
            for context_provider in self.context_providers.values()
            if isinstance(context_provider, BaseCommandContextProvider)
        ]
        options.sort(key=lambda opt: opt.id)
        return options

    def _make_autocomplete_option(
        self,
        id: str,
        description: str,
        only_start: bool,
        requires_arg: bool,
    ):
        label = id + (":" if requires_arg else " ")
        return ListOptionsEntry(
            id=id, description=description, label=label, only_start=only_start
        )
