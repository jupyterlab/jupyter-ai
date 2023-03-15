from typing import List, TypedDict

class DefaultTaskDefinition(TypedDict):
    id: str
    name: str
    prompt_template: str
    modality: str
    insertion_mode: str

tasks: List[DefaultTaskDefinition] = [
    {
        "id": "explain-code",
        "name": "Explain code",
        "prompt_template": "Explain the following Python 3 code. The first sentence must begin with the phrase \"The code below\".\n{body}",
        "modality": "txt2txt",
        "insertion_mode": "above"
    },
    {
        "id": "generate-code",
        "name": "Generate code",
        "prompt_template": "Generate Python 3 code in Markdown according to the following definition.\n{body}",
        "modality": "txt2txt",
        "insertion_mode": "below"
    },
    {
        "id": "explain-code-in-cells-above",
        "name": "Explain code in cells above",
        "prompt_template": "Explain the following Python 3 code. The first sentence must begin with the phrase \"The code below\".\n{body}",
        "modality": "txt2txt",
        "insertion_mode": "above-in-cells"
    },
    {
        "id": "generate-code-in-cells-below",
        "name": "Generate code in cells below",
        "prompt_template": "Generate Python 3 code in Markdown according to the following definition.\n{body}",
        "modality": "txt2txt",
        "insertion_mode": "below-in-cells"
    },
    {
        "id": "freeform",
        "name": "Freeform prompt",
        "prompt_template": "{body}",
        "modality": "txt2txt",
        "insertion_mode": "below"
    }
]
