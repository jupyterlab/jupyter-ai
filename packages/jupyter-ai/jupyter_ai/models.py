from typing import Optional

from pydantic import BaseModel

DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 100


# TODO: Delete this once the new Models API can return these properties.
# This is just being kept as a reference.
class ListProvidersEntry(BaseModel):
    """Model provider with supported models
    and provider's authentication strategy
    """

    id: str
    name: str
    model_id_label: Optional[str] = None
    models: list[str]
    help: Optional[str] = None
    # auth_strategy: AuthStrategy
    registry: bool
    # fields: list[Field]
    chat_models: Optional[list[str]] = None
    completion_models: Optional[list[str]] = None

