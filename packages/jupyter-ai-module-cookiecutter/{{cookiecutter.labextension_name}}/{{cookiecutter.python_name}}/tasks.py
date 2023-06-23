from typing import List

from jupyter_ai import DefaultTaskDefinition

# tasks your AI module exposes by default. declared in `pyproject.toml` as an
# entry point.
tasks: List[DefaultTaskDefinition] = [
    {
        "id": "test",
        "name": "Test task",
        "prompt_template": "{body}",
        "modality": "txt2txt",
        "insertion_mode": "test",
    }
]
