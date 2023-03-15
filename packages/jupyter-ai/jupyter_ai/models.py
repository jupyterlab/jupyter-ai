from pydantic import BaseModel
from typing import Dict, List

class PromptRequest(BaseModel):
    task_id: str
    engine_id: str
    prompt_variables: Dict[str, str]

class ListEnginesEntry(BaseModel):
    id: str
    name: str

class ListTasksEntry(BaseModel):
    id: str
    name: str

class ListTasksResponse(BaseModel):
    tasks: List[ListTasksEntry]

class DescribeTaskResponse(BaseModel):
    name: str
    insertion_mode: str
    prompt_template: str
    engines: List[ListEnginesEntry]
