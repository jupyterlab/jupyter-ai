import json
import os
import time
from uuid import uuid4

import ray
from ray.util.queue import Queue

from langchain.llms import BaseLLM
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.llms import BaseLLM
from langchain.chains import LLMChain

from nbformat.v4.nbbase import (
    nbformat,
    new_code_cell,
    new_markdown_cell,
    new_notebook
)

from jupyter_ai.models import AgentChatMessage, HumanChatMessage
from jupyter_ai.actors.base import BaseActor, Logger
from jupyter_ai_magics.providers import ChatOpenAINewProvider

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
    """Chain to generates tasks."""

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
            input_variables=[
                "description",
                "schema"
            ],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)

def generate_outline(description, llm=None, verbose=False):
    if llm is None:
        llm = ChatOpenAINewProvider(model_id='gpt-3.5-turbo')
    chain = NotebookOutlineChain.from_llm(llm)
    outline = chain.predict(description=description, schema=schema)
    return json.loads(outline)

class NotebookSectionCodeChain(LLMChain):
    """Chain to generates tasks."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, verbose: bool = True) -> LLMChain:
        task_creation_template = (
            "You are an AI that writes code for a single section of a Jupyter notebook.\n"
            "Overall topic of the notebook: {description}\n"
            "Title of the notebook section: {title}\n"
            "Description of the notebok section: {content}\n"
            "Given this information, write all the code for this section and this section only."
            " Your output should be valid code with inline comments.\n"
            "Code in the notebook so far:\n"
            "{code_so_far}"
        )
        prompt = PromptTemplate(
            template=task_creation_template,
            input_variables=[
                "description",
                "title",
                "content",
                "code_so_far"
            ],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)

def generate_code(outline, llm=None, verbose=False):
    if llm is None:
        llm = ChatOpenAINewProvider(model_id='gpt-3.5-turbo')
    chain = NotebookSectionCodeChain.from_llm(llm)
    code_so_far = []
    for section in outline['sections']:
        code = chain.predict(
            description=outline['description'],
            title=section['title'],
            content=section['content'],
            code_so_far='\n'.join(code_so_far)
        )
        section['code'] = code
        code_so_far.append(code)
    return outline

class NotebookSummaryChain(LLMChain):
    """Chain to generates tasks."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, verbose: bool=False) -> LLMChain:
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
    """Chain to generates tasks."""

    @classmethod
    def from_llm(cls, llm: BaseLLM, verbose: bool = True) -> LLMChain:
        task_creation_template = (
            "Create a short, few word, descriptive title for a Jupyter notebook with the following content."
            "Content:\n{content}"
        )
        prompt = PromptTemplate(
            template=task_creation_template,
            input_variables=[
                "content",
            ],
        )
        return cls(prompt=prompt, llm=llm, verbose=verbose)

def generate_title_and_summary(outline, llm=None, verbose=False):
    if llm is None:
        llm = ChatOpenAINewProvider(model_id='gpt-3.5-turbo')
    summary_chain = NotebookSummaryChain.from_llm(llm)
    title_chain = NotebookTitleChain.from_llm(llm)
    summary = summary_chain.predict(content=outline)
    title = title_chain.predict(content=outline)
    outline['summary'] = summary
    outline['title'] = title
    return outline

def create_notebook(outline):
    nb = new_notebook()
    markdown_cell = new_markdown_cell('# ' + outline['title'])
    nb['cells'].append(markdown_cell)
    markdown_cell = new_markdown_cell(outline['summary'])
    nb['cells'].append(markdown_cell)

    for section in outline['sections'][1:]:
        markdown_cell = new_markdown_cell('## ' + section['title'])
        nb['cells'].append(markdown_cell)
        code_cell = new_code_cell(section['code'])
        nb['cells'].append(code_cell)
    return nb

@ray.remote
class AutoNotebookActor(BaseActor):
    def __init__(self, reply_queue: Queue, root_dir: str, log: Logger):
        super().__init__(log=log, reply_queue=reply_queue)
        self.root_dir = root_dir
        self.llm = ChatOpenAINewProvider(model_id='gpt-3.5-turbo')
  
    def process_message(self, message: HumanChatMessage):
        outline = generate_outline(message.body, llm=self.llm)
        outline = generate_code(outline, llm=self.llm)
        outline = generate_title_and_summary(outline, llm=self.llm)
        notebook = create_notebook(outline)
        final_path = os.path.join(self.root_dir, outline['title'] + '.ipynb')
        nbformat.write(notebook, final_path)
        response = f"""🎉 I have created the notebook and saved it to the location {final_path}."""
        agent_message = AgentChatMessage(
                id=uuid4().hex,
                time=time.time(),
                body=response,
                reply_to=message.id
            )
        self.reply_queue.put(agent_message)
