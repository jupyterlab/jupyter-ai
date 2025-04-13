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
            description="The standard agent provided by JupyterLab. Currently has no tools.",
            system_prompt="..."
        )
    
    async def process_message(self):
        self.log.info("HI IM JUPYTERNAUT AND IDK WHAT TO DO")
        return
