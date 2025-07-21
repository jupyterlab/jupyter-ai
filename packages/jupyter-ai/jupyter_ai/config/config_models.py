from typing import Any, Optional

from pydantic import BaseModel, field_validator


class JaiConfig(BaseModel):
    """
    Pydantic model that serializes and validates the Jupyter AI config.
    """

    model_provider_id: Optional[str] = None
    """
    Model ID of the chat model.
    """

    embeddings_provider_id: Optional[str] = None
    """
    Model ID of the embedding model.
    """

    completions_model_provider_id: Optional[str] = None
    """
    Model ID of the completions model.
    """

    api_keys: dict[str, str] = {}
    """
    Dictionary of API keys. The name of each key should correspond to the
    environment variable expected by the underlying client library, e.g.
    "OPENAI_API_KEY".
    """

    send_with_shift_enter: bool = False
    """
    Whether the "Enter" key should create a new line instead of sending the
    message.
    """

    fields: dict[str, dict[str, Any]] = {}
    """
    Dictionary that defines custom fields for each chat model.
    Key: chat model ID.
    Value: Dictionary of keyword arguments.
    """

    embeddings_fields: dict[str, dict[str, Any]] = {}
    completions_fields: dict[str, dict[str, Any]] = {}


class DescribeConfigResponse(BaseModel):
    model_provider_id: Optional[str] = None
    embeddings_provider_id: Optional[str] = None
    send_with_shift_enter: bool
    fields: dict[str, dict[str, Any]]

    api_keys: list[str]
    """
    List of the names of the API keys. This deliberately does not include the
    value of each API key in the interest of security.
    """

    last_read: int
    """
    Timestamp indicating when the configuration file was last read. Should be
    passed to the subsequent UpdateConfig request if an update is made.
    """

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
