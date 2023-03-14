import openai
from traitlets.config import Unicode

from typing import Dict

from jupyter_ai.engine import BaseModelEngine
from jupyter_ai.models import DescribeTaskResponse

class ChatGptModelEngine(BaseModelEngine):
    id = "chatgpt"
    name = "ChatGPT"
    modalities = [
        "txt2txt"
    ]

    api_key = Unicode(
        config=True,
        help="OpenAI API key",
        allow_none=False
    )

    async def execute(self, task: DescribeTaskResponse, prompt_variables: Dict[str, str]):
        if "body" not in prompt_variables:
            raise Exception("Prompt body must be specified.")

        prompt = task.prompt_template.format(**prompt_variables)
        self.log.info(f"ChatGPT prompt:\n{prompt}")
        
        openai.api_key = self.api_key
        completion = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return completion.choices[0].message.content
