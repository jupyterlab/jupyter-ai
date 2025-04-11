from .base_persona import BasePersona, PersonaDefaults

class JupyternautPersona(BasePersona):
    """
    The Jupyternaut persona, the main persona provided by Jupyter AI.
    """

    @property
    def id(self):
        return "jupyter-ai:jupyternaut"
    
    @property
    def defaults(self):
        return PersonaDefaults(
            name="Jupyternaut",
            avatar_path="/api/ai/static/jupyternaut.svg",
            system_prompt="..."
        )
    
