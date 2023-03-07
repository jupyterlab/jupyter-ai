import openai
from traitlets.config import Unicode

from typing import List, Dict

from jupyter_ai.engine import BaseModelEngine, DefaultTaskDefinition
from jupyter_ai.models import DescribeTaskResponse

class ChatGptModelEngine(BaseModelEngine):
    name = "chatgpt"
    input_type = "txt"
    output_type = "txt"

    api_key = Unicode(
        config=True,
        help="OpenAI API key",
        allow_none=False
    )

    def list_default_tasks(self) -> List[DefaultTaskDefinition]:
        # Tasks your model engine provides by default.
        return [
            {
                "id": "explain-code",
                "name": "Explain code",
                "prompt_template": "Explain the following Python 3 code. The first sentence must begin with the phrase \"The code below\".\n{body}",
                "insertion_mode": "above"
            },
            {
                "id": "generate-code",
                "name": "Generate code",
                "prompt_template": "Generate Python 3 code in Markdown according to the following definition.\n{body}",
                "insertion_mode": "below"
            },
            {
                "id": "explain-code-in-cells-above",
                "name": "Explain code in cells above",
                "prompt_template": "Explain the following Python 3 code. The first sentence must begin with the phrase \"The code below\".\n{body}",
                "insertion_mode": "above-in-cells"
            },
            {
                "id": "generate-code-in-cells-below",
                "name": "Generate code in cells below",
                "prompt_template": "Generate Python 3 code in Markdown according to the following definition.\n{body}",
                "insertion_mode": "below-in-cells"
            },
            {
                "id": "freeform",
                "name": "Freeform prompt",
                "prompt_template": "{body}",
                "insertion_mode": "below"
            }
        ]

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
