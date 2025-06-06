from typing import Any, Optional

# unused import: exports Persona from this module
from jupyter_ai_magics.models.persona import Persona
from jupyter_ai_magics.providers import AuthStrategy, Field
from pydantic import BaseModel, field_validator

DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 100


class ListProvidersEntry(BaseModel):
    """Model provider with supported models
    and provider's authentication strategy
    """

    id: str
    name: str
    model_id_label: Optional[str] = None
    models: list[str]
    help: Optional[str] = None
    auth_strategy: AuthStrategy
    registry: bool
    fields: list[Field]
    chat_models: Optional[list[str]] = None
    completion_models: Optional[list[str]] = None


class ListProvidersResponse(BaseModel):
    providers: list[ListProvidersEntry]


class IndexedDir(BaseModel):
    path: str
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP


class IndexMetadata(BaseModel):
    dirs: list[IndexedDir]


class DescribeConfigResponse(BaseModel):
    model_provider_id: Optional[str] = None
    embeddings_provider_id: Optional[str] = None
    send_with_shift_enter: bool
    fields: dict[str, dict[str, Any]]
    # when sending config over REST API, do not include values of the API keys,
    # just the names.
    api_keys: list[str]
    # timestamp indicating when the configuration file was last read. should be
    # passed to the subsequent UpdateConfig request.
    last_read: int
    completions_model_provider_id: Optional[str] = None
    completions_fields: dict[str, dict[str, Any]]
    embeddings_fields: dict[str, dict[str, Any]]


class UpdateConfigRequest(BaseModel):
    model_provider_id: Optional[str] = None
    embeddings_provider_id: Optional[str] = None
    completions_model_provider_id: Optional[str] = None
    send_with_shift_enter: Optional[bool] = None
    api_keys: Optional[dict[str, str]] = None
    # if passed, this will raise an Error if the config was written to after the
    # time specified by `last_read` to prevent write-write conflicts.
    last_read: Optional[int] = None
    fields: Optional[dict[str, dict[str, Any]]] = None
    completions_fields: Optional[dict[str, dict[str, Any]]] = None
    embeddings_fields: Optional[dict[str, dict[str, Any]]] = None

    @field_validator("send_with_shift_enter", "api_keys", "fields", mode="before")
    @classmethod
    def ensure_not_none_if_passed(cls, field_val: Any) -> Any:
        """
        Field validator ensuring that certain fields are never `None` if set.
        """
        assert field_val is not None, "size may not be None"
        return field_val


class GlobalConfig(BaseModel):
    """Model used to represent the config by ConfigManager. This is exclusive to
    the backend and should never be sent to the client."""

    model_provider_id: Optional[str] = None
    embeddings_provider_id: Optional[str] = None
    send_with_shift_enter: bool
    fields: dict[str, dict[str, Any]]
    api_keys: dict[str, str]
    completions_model_provider_id: Optional[str] = None
    completions_fields: dict[str, dict[str, Any]]
    embeddings_fields: dict[str, dict[str, Any]]
