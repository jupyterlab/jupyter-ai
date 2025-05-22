import ast
import asyncio
import os
import time
import traceback
from pathlib import Path
from typing import Optional

import nbformat
from jupyter_ai.chat_handlers import BaseChatHandler, SlashCommandRoutingType
from jupyter_ai.models import HumanChatMessage
from jupyter_ai_magics.providers import BaseProvider
from langchain.chains import LLMChain
from langchain.llms import BaseLLM
from langchain.output_parsers import PydanticOutputParser
from langchain.schema.output_parser import BaseOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel


class OutlineSection(BaseModel):
    title: str
    content: str


class Outline(BaseModel):
    description: Optional[str] = None
    sections: list[OutlineSection]


class NotebookOutlineChain(LLMChain):
    """Chain to generate a notebook outline, with section titles and descriptions."""

    @classmethod
    def from_llm(
        cls, llm: BaseLLM, parser: BaseOutputParser[Outline], verbose: bool = False
    ) -> LLMChain:
        task_creation_template = (
            "You are an AI that creates a detailed content outline for a Jupyter notebook on a given topic.\n"
            "{format_instructions}\n"
            "Here is a description of the notebook you will create an outline for: {description}\n"
            "Don't include an introduction or conclusion section in the outline, focus only on description and sections that will need code.\n"
        )
        prompt = PromptTemplate(
            template=task_creation_template,
            input_variables=["description"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)


async def generate_outline(description, llm=None, verbose=False):
    """Generate an outline of sections given a description of a notebook."""
    parser = PydanticOutputParser(pydantic_object=Outline)
    chain = NotebookOutlineChain.from_llm(llm=llm, parser=parser, verbose=verbose)
    outline = await chain.apredict(description=description)
    outline = parser.parse(outline)
    return outline.model_dump()


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
            "Content:\n{content}\n"
            "Don't return anything other than the title."
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
    """Generate a title of a notebook outline using an LLM."""
    title_chain = NotebookTitleChain.from_llm(llm=llm, verbose=verbose)
    title = await title_chain.apredict(content=outline)
    title = title.strip()
    title = title.strip("'\"")
    outline["title"] = title


async def generate_summary(outline, llm=None, verbose: bool = False):
    """Generate a summary of a notebook using an LLM."""
    summary_chain = NotebookSummaryChain.from_llm(llm=llm, verbose=verbose)
    summary = await summary_chain.apredict(content=outline)
    outline["summary"] = summary


async def fill_outline(outline, llm, verbose=False):
    """Generate title and content of a notebook sections using an LLM."""
    shared_kwargs = {"outline": outline, "llm": llm, "verbose": verbose}

    await generate_title(**shared_kwargs)
    await generate_summary(**shared_kwargs)
    for section in outline["sections"]:
        await generate_code(section, outline["description"], llm=llm, verbose=verbose)


async def afill_outline(outline, llm, verbose=False):
    """Concurrently generate title and content of notebook sections using an LLM."""
    shared_kwargs = {"outline": outline, "llm": llm, "verbose": verbose}

    all_coros = []
    all_coros.append(generate_title(**shared_kwargs))
    all_coros.append(generate_summary(**shared_kwargs))
    for section in outline["sections"]:
        all_coros.append(
            generate_code(section, outline["description"], llm=llm, verbose=verbose)
        )
    await asyncio.gather(*all_coros)


# Check if the content of the cell is python code or not
def is_not_python_code(source: str) -> bool:
    try:
        ast.parse(source)
    except:
        return True
    return False


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

    # Post process notebook for hanging code cells: merge hanging cell with the previous cell
    merged_cells = []
    for cell in nb["cells"]:
        # Fix a hanging code cell
        follows_code_cell = merged_cells and merged_cells[-1]["cell_type"] == "code"
        is_incomplete = cell["cell_type"] == "code" and cell["source"].startswith(" ")
        if follows_code_cell and is_incomplete:
            merged_cells[-1]["source"] = (
                merged_cells[-1]["source"] + "\n\n" + cell["source"]
            )
        else:
            merged_cells.append(cell)

    # Fix code cells that should be markdown
    for cell in merged_cells:
        if cell["cell_type"] == "code" and is_not_python_code(cell["source"]):
            cell["cell_type"] = "markdown"

    nb["cells"] = merged_cells
    return nb


class GenerateChatHandler(BaseChatHandler):
    id = "generate"
    name = "Generate Notebook"
    help = "Generate a Jupyter notebook from a text prompt"
    routing_type = SlashCommandRoutingType(slash_id="generate")

    uses_llm = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm: Optional[BaseProvider] = None

    def create_llm_chain(
        self, provider: type[BaseProvider], provider_params: dict[str, str]
    ):
        unified_parameters = {
            **provider_params,
            **(self.get_model_parameters(provider, provider_params)),
        }
        llm = provider(**unified_parameters)

        self.llm = llm
        return llm

    async def _generate_notebook(self, prompt: str):
        """Generate a notebook and save to local disk"""

        # create outline
        outline = await generate_outline(prompt, llm=self.llm, verbose=True)
        # Save the user input prompt, the description property is now LLM generated.
        outline["prompt"] = prompt

        assert self.llm
        if self.llm.allows_concurrency:
            # fill the outline concurrently
            await afill_outline(outline, llm=self.llm, verbose=True)
        else:
            # fill outline
            await fill_outline(outline, llm=self.llm, verbose=True)

        # create and write the notebook to disk
        notebook = create_notebook(outline)
        final_path = os.path.join(self.output_dir, outline["title"] + ".ipynb")
        nbformat.write(notebook, final_path)
        return final_path

    async def process_message(self, message: HumanChatMessage):
        self.get_llm_chain()

        # first send a verification message to user
        response = "👍 Great, I will get started on your notebook. It may take a few minutes, but I will reply here when the notebook is ready. In the meantime, you can continue to ask me other questions."
        self.reply(response, message)

        final_path = await self._generate_notebook(prompt=message.body)
        response = f"""🎉 I have created your notebook and saved it to the location {final_path}. I am still learning how to create notebooks, so please review all code before running it."""
        self.reply(response, message)

    async def handle_exc(self, e: Exception, message: HumanChatMessage):
        timestamp = time.strftime("%Y-%m-%d-%H.%M.%S")
        default_log_dir = Path(self.output_dir) / "jupyter-ai-logs"
        log_dir = self.log_dir or default_log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"generate-{timestamp}.log"
        with log_path.open("w") as log:
            traceback.print_exc(file=log)

        response = f"An error occurred while generating the notebook. The error details have been saved to `./{log_path}`.\n\nTry running `/generate` again, as some language models require multiple attempts before a notebook is generated."
        self.reply(response, message)
