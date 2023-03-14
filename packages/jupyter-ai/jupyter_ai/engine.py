from abc import abstractmethod, ABC, ABCMeta
from typing import Dict
import openai
from traitlets.config import LoggingConfigurable, Unicode
from .task_manager import DescribeTaskResponse

class BaseModelEngineMetaclass(ABCMeta, type(LoggingConfigurable)):
    pass

class BaseModelEngine(ABC, LoggingConfigurable, metaclass=BaseModelEngineMetaclass):
    id: str
    name: str

    # these two attributes are currently reserved but unused.
    input_type: str
    output_type: str
  
    @abstractmethod
    async def execute(self, task: DescribeTaskResponse, prompt_variables: Dict[str, str]):
        pass

class GPT3ModelEngine(BaseModelEngine):
    id = "gpt3"
    name = "GPT-3"
    modalities = [
        "txt2txt"
    ]

    api_key = Unicode(
        config=True,
        help="OpenAI API key",
        allow_none=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def execute(self, task: DescribeTaskResponse, prompt_variables: Dict[str, str]):
        if "body" not in prompt_variables:
            raise Exception("Prompt body must be specified.")

        prompt = task.prompt_template.format(**prompt_variables)
        self.log.info(f"GPT3 prompt:\n{prompt}")
        
        openai.api_key = self.api_key
        response = await openai.Completion.acreate(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0.7,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response['choices'][0]['text']