from pydantic import BaseModel


class SecretsList(BaseModel):
    """
    The response type returned by `GET /api/ai/secrets`.
    """

    dotenv_secrets: list[str]
    """
    List of secret names set in the `.env` file. These secrets can be edited.
    """

    process_secrets: list[str]
    """
    List of secret names passed as environment variables to the Python process.
    This includes any environment variable whose name contains 'KEY' or 'TOKEN'
    or 'SECRET'. These secrets cannot be edited.
    """


class UpdateSecretsRequest(BaseModel):
    """
    The request body expected by `PUT /api/ai/secrets`.
    """
    updated_secrets: dict[str, str]
