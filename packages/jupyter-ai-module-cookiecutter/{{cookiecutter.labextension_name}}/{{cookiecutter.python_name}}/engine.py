from typing import Dict

from jupyter_ai.engine import BaseModelEngine
from jupyter_ai.models import DescribeTaskResponse


class TestModelEngine(BaseModelEngine):
    name = "test"
    input_type = "txt"
    output_type = "txt"

    # BaseModelEngine is also a traitlets.config.Configurable object, so you can
    # also expose configurable traits on the class definition like so:
    #
    # api_key = Unicode(
    #     config=True,
    #     help="OpenAI API key",
    #     allow_none=False
    # )
    #

    async def execute(
        self, task: DescribeTaskResponse, prompt_variables: Dict[str, str]
    ):
        # Core method that executes a model when provided with a task
        # description and a dictionary of prompt variables. For example, to
        # execute an OpenAI text completion model:
        #
        # prompt = task.prompt_template.format(**prompt_variables)
        # openai.api_key = self.api_key
        # response = openai.Completion.create(
        #     model="text-davinci-003",
        #     prompt=prompt,
        #     ...
        # )
        # return response['choices'][0]['text']

        return "test output"
