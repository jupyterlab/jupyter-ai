from jupyter_ai.personas.base_persona import BasePersona, PersonaDefaults

class DebugPersona(BasePersona):
    """
    The Jupyternaut persona, the main persona provided by Jupyter AI.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def id(self):
        return "jupyter-ai-test:debug"
    
    @property
    def defaults(self):
        return PersonaDefaults(
            name="DebugPersona",
            avatar_path="/api/ai/static/jupyternaut.svg",
            description="A mock persona used for debugging in local dev environments.",
            system_prompt="..."
        )
    
    async def process_message(self):
        self.log.info("HI IM DEBUGPERSONA AND IDK WHAT TO DO")
        return
