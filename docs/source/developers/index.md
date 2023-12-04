# Developers

The developer documentation is for authors who want to enhance
the functionality of Jupyter AI.

If you are interested in contributing to Jupyter AI,
please see our {doc}`contributor's guide </contributors/index>`.

## Pydantic compatibility

Jupyter AI is fully compatible with Python environments using Pydantic v1
or Pydantic v2. Jupyter AI imports Pydantic classes from the
`langchain.pydantic_v1` module. Developers should do the same when they extend
Jupyter AI classes.

For more details about using `langchain.pydantic_v1` in an environment with
Pydantic v2 installed, see the
[LangChain documentation on Pydantic compatibility](https://python.langchain.com/docs/guides/pydantic_compatibility).

## Prompt templates

Each provider can define **prompt templates** for each supported format. A prompt
template guides the language model to produce output in a particular
format. The default prompt templates are a
[Python dictionary mapping formats to templates](https://github.com/jupyterlab/jupyter-ai/blob/57a758fa5cdd5a87da5519987895aa688b3766a8/packages/jupyter-ai-magics/jupyter_ai_magics/providers.py#L138-L166).
Developers who write subclasses of `BaseProvider` can override templates per
output format, per model, and based on the prompt being submitted, by
implementing their own
[`get_prompt_template` function](https://github.com/jupyterlab/jupyter-ai/blob/57a758fa5cdd5a87da5519987895aa688b3766a8/packages/jupyter-ai-magics/jupyter_ai_magics/providers.py#L186-L195).
Each prompt template includes the string `{prompt}`, which is replaced with
the user-provided prompt when the user runs a magic command.

### Customizing prompt templates

To modify the prompt template for a given format, override the `get_prompt_template` method:

```python
from langchain.prompts import PromptTemplate


class MyProvider(BaseProvider, FakeListLLM):
    # (... properties as above ...)
    def get_prompt_template(self, format) -> PromptTemplate:
        if format === "code":
            return PromptTemplate.from_template(
                "{prompt}\n\nProduce output as source code only, "
                "with no text or explanation before or after it."
            )
        return super().get_prompt_template(format)
```

Please note that this will only work with Jupyter AI magics (the `%ai` and `%%ai` magic commands). Custom prompt templates are not used in the chat interface yet.
