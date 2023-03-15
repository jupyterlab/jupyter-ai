from typing import List
from jupyter_ai import DefaultTaskDefinition

tasks: List[DefaultTaskDefinition] = [
    {
        "id": "generate-image",
        "name": "Generate image below",
        "prompt_template": "{body}",
        "modality": "txt2img",
        "insertion_mode": "below-in-image"
    },
    {
        "id": "generate-photorealistic-image",
        "name": "Generate photorealistic image below",
        "prompt_template": "{body} in a photorealistic style",
        "modality": "txt2img",
        "insertion_mode": "below-in-image"
    },
    {
        "id": "generate-cartoon-image",
        "name": "Generate cartoon image below",
        "prompt_template": "{body} in the style of a cartoon",
        "modality": "txt2img",
        "insertion_mode": "below-in-image"
    }
]
