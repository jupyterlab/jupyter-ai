import os
from typing import ClassVar

from langchain.pydantic_v1 import BaseModel

JUPYTERNAUT_AVATAR_PATH = str(
    os.path.join(os.path.dirname(__file__), "..", "static", "jupyternaut.svg")
)
JUPYTERNAUT_AVATAR_ROUTE = "api/ai/static/jupyternaut.svg"


class Persona(BaseModel):
    """
    Model of an **agent persona**, a struct that includes the name & avatar
    shown on agent replies in the chat UI.

    Each persona is specific to a single provider, set on the `persona` field.
    """

    name: ClassVar[str] = ...
    """
    Name of the persona, e.g. "Jupyternaut". This is used to render the name
    shown on agent replies in the chat UI.
    """

    avatar_route: ClassVar[str] = ...
    """
    The server route that should be used the avatar of this persona. This is
    used to render the avatar shown on agent replies in the chat UI.
    """

    avatar_path: ClassVar[str] = ...
    """
    The path to the avatar SVG file on the server filesystem. The server should
    serve the file at this path on the route specified by `avatar_route`.
    """


class JupyternautPersona(Persona):
    name: ClassVar[str] = "Jupyternaut"
    avatar_route: ClassVar[str] = JUPYTERNAUT_AVATAR_ROUTE
    avatar_path: ClassVar[str] = JUPYTERNAUT_AVATAR_PATH
