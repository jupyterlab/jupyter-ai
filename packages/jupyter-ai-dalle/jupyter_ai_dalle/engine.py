from typing import Dict
from traitlets.config import Unicode
import openai

from jupyter_ai.engine import BaseModelEngine
from jupyter_ai.models import DescribeTaskResponse

class DalleModelEngine(BaseModelEngine):
    id = "dalle"
    name = "DALL-E"
    modalities = [
        "txt2img"
    ]

    api_key = Unicode(
        config=True,
        help="OpenAI API key",
        allow_none=False
    )

    async def execute(self, task: DescribeTaskResponse, prompt_variables: Dict[str, str]) -> str:
        if "body" not in prompt_variables:
            raise Exception("Prompt body must be specified.")

        prompt = task.prompt_template.format(**prompt_variables)
        self.log.info(f"DALL-E prompt:\n{prompt}")

        openai.api_key = self.api_key
        response = await openai.Image.acreate(
            prompt=prompt,
            n=1,
            size="512x512"
        )

        return response['data'][0]['url']
