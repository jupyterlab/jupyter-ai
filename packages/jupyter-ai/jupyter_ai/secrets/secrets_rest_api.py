from __future__ import annotations
from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from tornado.web import authenticated, HTTPError
from typing import TYPE_CHECKING
from .secrets_types import UpdateSecretsRequest

if TYPE_CHECKING:
    from .secrets_manager import EnvSecretsManager

class SecretsRestAPI(BaseAPIHandler):
    """
    Defines the REST API served at the `/api/ai/secrets` endpoint.

    Methods supported:

    - `GET secrets/`: Returns a list of secrets.
    - `PUT secrets/`: Add/update/delete a set of secrets.
    """

    @property
    def secrets_manager(self) -> EnvSecretsManager:  # type:ignore[override]
        return self.settings["jai_secrets_manager"]

    @authenticated
    def get(self):
        response = self.secrets_manager.list_secrets()
        self.set_status(200)
        self.finish(response.model_dump_json())

    @authenticated
    async def put(self):
        try:
            # Validate the request body matches the `UpdateSecretsRequest`
            # expected type
            request = UpdateSecretsRequest(**self.get_json_body())

            # Dispatch the request to the secrets manager
            await self.secrets_manager.update_secrets(request.updated_secrets)
        except Exception as e:
            self.log.exception("Exception raised when handling PUT /api/ai/secrets/:")
            raise HTTPError(500, str(e))

        self.set_status(204)
        self.finish()
