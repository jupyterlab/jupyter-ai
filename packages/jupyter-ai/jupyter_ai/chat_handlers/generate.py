import asyncio
import json
import os
from typing import Dict, Type

import nbformat
from jupyter_ai.chat_handlers import BaseChatHandler
from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.chains import LLMChain
from langchain.llms import BaseLLM
from langchain.prompts import PromptTemplate

schema = """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "description": {
      "type": "string"
    },
    "sections": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "title": {
            "type": "string"
          },
          "content": {
            "type": "string"
          }
        },
        "required": ["title", "content"]
      }
    }
  },
  "required": ["sections"]
}"""


class NotebookOutlineChain(LLMChain):
    """Chain to generate a notebook outline, with section titles and descriptions."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, verbose: bool = False) -> LLMChain:
        task_creation_template = (
            "You are an AI that creates a detailed content outline for a Jupyter notebook on a given topic.\n"
            "Generate the outline as JSON data that will validate against this JSON schema:\n"
            "{schema}\n"
            "Here is a description of the notebook you will create an outline for: {description}\n"
            "Don't include an introduction or conclusion section in the outline, focus only on sections that will need code."
        )
        prompt = PromptTemplate(
            template=task_creation_template,
            input_variables=["description", "schema"],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)


async def generate_outline(description, llm=None, verbose=False):
    """Generate an outline of sections given a description of a notebook."""
    chain = NotebookOutlineChain.from_llm(llm=llm, verbose=verbose)
    outline = await chain.apredict(description=description, schema=schema)
    return json.loads(outline)


class CodeImproverChain(LLMChain):
    """Chain to improve source code."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, verbose: bool = False) -> LLMChain:
        task_creation_template = (
            "Improve the following code and make sure it is valid. Make sure to return the improved code only - don't give an explanation of the improvements.\n"
            "{code}"
        )
        prompt = PromptTemplate(
            template=task_creation_template,
            input_variables=[
                "code",
            ],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)


class NotebookSectionCodeChain(LLMChain):
    """Chain to generate source code for a notebook section."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, verbose: bool = False) -> LLMChain:
        task_creation_template = (
            "You are an AI that writes code for a single section of a Jupyter notebook.\n"
            "Overall topic of the notebook: {description}\n"
            "Title of the notebook section: {title}\n"
            "Description of the notebok section: {content}\n"
            "Given this information, write all the code for this section and this section only."
            " Your output should be valid code with inline comments.\n"
        )
        prompt = PromptTemplate(
            template=task_creation_template,
            input_variables=["description", "title", "content"],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)


class NotebookSummaryChain(LLMChain):
    """Chain to generate a short summary of a notebook."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, verbose: bool = False) -> LLMChain:
        task_creation_template = (
            "Create a markdown summary for a Jupyter notebook with the following content."
            " The summary should consist of a single paragraph.\n"
            "Content:\n{content}"
        )
        prompt = PromptTemplate(
            template=task_creation_template,
            input_variables=[
                "content",
            ],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)


class NotebookTitleChain(LLMChain):
    """Chain to generate the title of a notebook."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, verbose: bool = False) -> LLMChain:
        task_creation_template = (
            "Create a short, few word, descriptive title for a Jupyter notebook with the following content.\n"
            "Content:\n{content}"
        )
        prompt = PromptTemplate(
            template=task_creation_template,
            input_variables=[
                "content",
            ],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)


async def improve_code(code, llm=None, verbose=False):
    """Improve source code using an LLM."""
    chain = CodeImproverChain.from_llm(llm=llm, verbose=verbose)
    improved_code = await chain.apredict(code=code)
    improved_code = "\n".join(
        [line for line in improved_code.split("\n") if not line.startswith("```")]
    )
    return improved_code


async def generate_code(section, description, llm=None, verbose=False) -> None:
    """
    Function that accepts a section and adds code under the "code" key when
    awaited.
    """
    chain = NotebookSectionCodeChain.from_llm(llm=llm, verbose=verbose)
    code = await chain.apredict(
        description=description,
        title=section["title"],
        content=section["content"],
    )
    improved_code = await improve_code(code, llm=llm, verbose=verbose)
    section["code"] = improved_code


async def generate_title(outline, llm=None, verbose: bool = False):
    """Generate a title and summary of a notebook outline using an LLM."""
    title_chain = NotebookTitleChain.from_llm(llm=llm, verbose=verbose)
    title = await title_chain.apredict(content=outline)
    title = title.strip()
    title = title.strip("'\"")
    outline["title"] = title


async def generate_summary(outline, llm=None, verbose: bool = False):
    summary_chain = NotebookSummaryChain.from_llm(llm=llm, verbose=verbose)
    summary = await summary_chain.apredict(content=outline)
    outline["summary"] = summary


async def fill_outline(outline, llm, verbose=False):
    shared_kwargs = {"outline": outline, "llm": llm, "verbose": verbose}

    all_coros = []
    all_coros.append(generate_title(**shared_kwargs))
    all_coros.append(generate_summary(**shared_kwargs))
    for section in outline["sections"]:
        all_coros.append(
            generate_code(section, outline["description"], llm=llm, verbose=verbose)
        )
    await asyncio.gather(*all_coros)


def create_notebook(outline):
    """Create an nbformat Notebook object for a notebook outline."""
    nbf = nbformat.v4
    nb = nbf.new_notebook()
    nb["cells"].append(nbf.new_markdown_cell("# " + outline["title"]))
    nb["cells"].append(nbf.new_markdown_cell("## Introduction"))
    disclaimer = f"This notebook was created by [Jupyter AI](https://github.com/jupyterlab/jupyter-ai) with the following prompt:\n\n> {outline['prompt']}"
    nb["cells"].append(nbf.new_markdown_cell(disclaimer))
    nb["cells"].append(nbf.new_markdown_cell(outline["summary"]))

    for section in outline["sections"][1:]:
        nb["cells"].append(nbf.new_markdown_cell("## " + section["title"]))
        for code_block in section["code"].split("\n\n"):
            nb["cells"].append(nbf.new_code_cell(code_block))
    return nb


class GenerateChatHandler(BaseChatHandler):
    """Generates a Jupyter notebook given a description."""

    def __init__(self, root_dir: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_dir = os.path.abspath(os.path.expanduser(root_dir))
        self.llm = None

    def create_llm_chain(
        self, provider: Type[BaseProvider], provider_params: Dict[str, str]
    ):
        llm = provider(**provider_params)
        self.llm = llm
        return llm

    async def _process_message(self, message: HumanChatMessage):
        self.get_llm_chain()

        # first send a verification message to user
        response = "👍 Great, I will get started on your notebook. It may take a few minutes, but I will reply here when the notebook is ready. In the meantime, you can continue to ask me other questions."
        self.reply(response, message)

        # generate notebook outline
        prompt = message.body
        outline = await generate_outline(prompt, llm=self.llm, verbose=True)
        # Save the user input prompt, the description property is now LLM generated.
        outline["prompt"] = prompt

        # fill the outline concurrently
        await fill_outline(outline, llm=self.llm, verbose=True)

        # create and write the notebook to disk
        notebook = create_notebook(outline)
        final_path = os.path.join(self.root_dir, outline["title"] + ".ipynb")
        nbformat.write(notebook, final_path)
        response = f"""🎉 I have created your notebook and saved it to the location {final_path}. I am still learning how to create notebooks, so please review all code before running it."""
        self.reply(response, message)


# /generate notebook
# Error handling
