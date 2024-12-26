from typing import Any, Dict, List, Optional

# unused import: exports Persona from this module
from jupyter_ai_magics.models.persona import Persona
from jupyter_ai_magics.providers import AuthStrategy, Field
from langchain.pydantic_v1 import BaseModel, validator

DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 100


class ListProvidersEntry(BaseModel):
    """Model provider with supported models
    and provider's authentication strategy
    """

    id: str
    name: str
    model_id_label: Optional[str]
    models: List[str]
    help: Optional[str]
    auth_strategy: AuthStrategy
    registry: bool
    fields: List[Field]
    chat_models: Optional[List[str]]
    completion_models: Optional[List[str]]


class ListProvidersResponse(BaseModel):
    providers: List[ListProvidersEntry]


class IndexedDir(BaseModel):
    path: str
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP


class IndexMetadata(BaseModel):
    dirs: List[IndexedDir]


class DescribeConfigResponse(BaseModel):
    model_provider_id: Optional[str]
    embeddings_provider_id: Optional[str]
    send_with_shift_enter: bool
    fields: Dict[str, Dict[str, Any]]
    # when sending config over REST API, do not include values of the API keys,
    # just the names.
    api_keys: List[str]
    # timestamp indicating when the configuration file was last read. should be
    # passed to the subsequent UpdateConfig request.
    last_read: int
    completions_model_provider_id: Optional[str]
    completions_fields: Dict[str, Dict[str, Any]]


def forbid_none(cls, v):
    assert v is not None, "size may not be None"
    return v


class UpdateConfigRequest(BaseModel):
    model_provider_id: Optional[str]
    embeddings_provider_id: Optional[str]
    send_with_shift_enter: Optional[bool]
    api_keys: Optional[Dict[str, str]]
    fields: Optional[Dict[str, Dict[str, Any]]]
    # if passed, this will raise an Error if the config was written to after the
    # time specified by `last_read` to prevent write-write conflicts.
    last_read: Optional[int]
    completions_model_provider_id: Optional[str]
    completions_fields: Optional[Dict[str, Dict[str, Any]]]

    _validate_send_wse = validator("send_with_shift_enter", allow_reuse=True)(
        forbid_none
    )
    _validate_api_keys = validator("api_keys", allow_reuse=True)(forbid_none)
    _validate_fields = validator("fields", allow_reuse=True)(forbid_none)


class GlobalConfig(BaseModel):
    """Model used to represent the config by ConfigManager. This is exclusive to
    the backend and should never be sent to the client."""

    model_provider_id: Optional[str]
    embeddings_provider_id: Optional[str]
    send_with_shift_enter: bool
    fields: Dict[str, Dict[str, Any]]
    api_keys: Dict[str, str]
    completions_model_provider_id: Optional[str]
    completions_fields: Dict[str, Dict[str, Any]]


class ListSlashCommandsEntry(BaseModel):
    slash_id: str
    description: str


class ListSlashCommandsResponse(BaseModel):
    slash_commands: List[ListSlashCommandsEntry] = []


class ListOptionsEntry(BaseModel):
    id: str
    """ID of the autocomplete option.
    Includes the command prefix. E.g. "/clear", "@file"."""
    label: str
    """Text that will be inserted into the prompt when the option is selected.
    Includes a space at the end if the option is complete.
    Partial suggestions do not include the space and may trigger future suggestions."""
    description: str
    """Text next to the option in the autocomplete list."""
    only_start: bool
    """Whether to command can only be inserted at the start of the prompt."""


class ListOptionsResponse(BaseModel):
    options: List[ListOptionsEntry] = []
