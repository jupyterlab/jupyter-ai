from typing import Optional

from jupyter_ai_magics.providers import AuthStrategy, Field
from pydantic import BaseModel

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
