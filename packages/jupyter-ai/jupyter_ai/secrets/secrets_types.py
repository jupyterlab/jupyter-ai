from typing import Optional

from pydantic import BaseModel


class SecretsList(BaseModel):
    """
    The response type returned by `GET /api/ai/secrets`.

    The response fields only include the names of each secret, and never must
    never include the value of any secret.
    """

    editable_secrets: list[str] = []
    """
    List of secrets set in the `.env` file. These secrets can be edited.
    """

    static_secrets: list[str] = []
    """
    List of secrets passed as environment variables to the Python process or
    passed as traitlets configuration to JupyterLab. These secrets cannot be
    edited.

    Environment variables passed to the Python process are only included if
    their name contains 'KEY' or 'TOKEN' or 'SECRET'.
    """


class UpdateSecretsRequest(BaseModel):
    """
    The request body expected by `PUT /api/ai/secrets`.
    """

    updated_secrets: dict[str, Optional[str]]
