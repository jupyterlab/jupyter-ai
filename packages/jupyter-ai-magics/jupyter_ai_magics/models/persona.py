from pydantic import BaseModel


class Persona(BaseModel):
    """
    Model of an **agent persona**, a struct that includes the name & avatar
    shown on agent replies in the chat UI.

    Each persona is specific to a single provider, set on the `persona` field.
    """

    name: str = ...
    """
    Name of the persona, e.g. "Jupyternaut". This is used to render the name
    shown on agent replies in the chat UI.
    """

    avatar_route: str = ...
    """
    The server route that should be used the avatar of this persona. This is
    used to render the avatar shown on agent replies in the chat UI.
    """


JUPYTERNAUT_AVATAR_ROUTE = "api/ai/static/jupyternaut.svg"
JupyternautPersona = Persona(name="Jupyternaut", avatar_route=JUPYTERNAUT_AVATAR_ROUTE)
