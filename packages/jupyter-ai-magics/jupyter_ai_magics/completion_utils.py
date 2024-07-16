from typing import Dict

from .models.completion import InlineCompletionRequest


def token_from_request(request: InlineCompletionRequest, suggestion: int):
    """Generate a deterministic token (for matching streamed messages)
    using request number and suggestion number"""
    return f"t{request.number}s{suggestion}"


def template_inputs_from_request(request: InlineCompletionRequest) -> Dict:
    suffix = request.suffix.strip()
    filename = request.path.split("/")[-1] if request.path else "untitled"

    return {
        "prefix": request.prefix,
        "suffix": suffix,
        "language": request.language,
        "filename": filename,
        "stop": ["\n```"],
    }


def post_process_suggestion(suggestion: str, request: InlineCompletionRequest) -> str:
    """Remove spurious fragments from the suggestion.

    While most models (especially instruct and infill models do not require
    any pre-processing, some models such as gpt-4 which only have chat APIs
    may require removing spurious fragments. This function uses heuristics
    and request data to remove such fragments.
    """
    # gpt-4 tends to add "```python" or similar
    language = request.language or "python"
    markdown_identifiers = {"ipython": ["ipython", "python", "py"]}
    bad_openings = [
        f"```{identifier}"
        for identifier in markdown_identifiers.get(language, [language])
    ] + ["```"]
    for opening in bad_openings:
        # ollama models tend to add spurious whitespace
        if suggestion.lstrip().startswith(opening):
            suggestion = suggestion.lstrip()[len(opening) :].lstrip()
            # check for the prefix inclusion (only if there was a bad opening)
            if suggestion.startswith(request.prefix):
                suggestion = suggestion[len(request.prefix) :]
            break

    # check if the suggestion ends with a closing markdown identifier and remove it
    if suggestion.rstrip().endswith("```"):
        suggestion = suggestion.rstrip()[:-3].rstrip()

    return suggestion
