from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING

from dotenv import dotenv_values
from dotenv.parser import parse_stream

if TYPE_CHECKING:
    import logging

ENVIRONMENT_VAR_REGEX = "^([a-zA-Z_][a-zA-Z_0-9]*)=?(['\"])?"
"""
Regex that matches a environment variable definition.
"""


def build_updated_dotenv(
    dotenv_content: str,
    updated_secrets: dict[str, str | None],
    log: logging.Logger | None = None,
) -> str | None:
    """
    Accepts the existing `.env` file as a parsed dictionary of environment
    variables, along with a dictionary of secrets to update. `None` values
    indicate the secret should be deleted. Otherwise, the secret will be added
    to or updated in `.env`.

    This function returns the content of the updated `.env` file as a string,
    and returns `None` if no updates to `.env` are required.

    NOTE: This function currently deletes inline comments on environment
    variable definitions. This may be fixed in a future update.
    """
    # Return early if no updates were given.
    if not updated_secrets:
        return None

    # Parse content of `.env` into a dictionary of environment variables
    dotenv_env = dotenv_values(stream=StringIO(dotenv_content))

    # Define `secrets_to_add`, `secrets_to_update`, and
    # `secrets_to_remove`.
    secrets_to_add: dict[str, str] = {}
    secrets_to_update: dict[str, str] = {}
    secrets_to_remove: set[str] = set()
    if dotenv_env:
        for name, value in updated_secrets.items():
            # Case 1: secret should be added to `.env`
            if value is not None and dotenv_env.get(name, None) == None:
                secrets_to_add[name] = value
                continue
            # Case 2: secret should be updated in `.env`
            if value is not None and dotenv_env.get(name, None) != None:
                secrets_to_update[name] = value
                continue
            # Case 3: secret should be removed from `.env`
            if value is None and dotenv_env.get(name, None) != None:
                secrets_to_remove.add(name)
                continue
    else:
        # Case 4: keys can only be added when a `.env` file is not
        # present.
        secrets_to_add = {k: v for k, v in updated_secrets.items() if v is not None}

    # Return early if update has effect.
    if not (secrets_to_add or secrets_to_update or secrets_to_remove):
        return None

    # First, handle the case of adding secrets to a new `.env` file.
    if not dotenv_env:
        new_content = ""
        max_i = len(secrets_to_add) - 1
        for i, (name, value) in enumerate(secrets_to_add.items()):
            new_content += f'{name}="{value}"\n'
            if i != max_i:
                new_content += "\n"

        return new_content

    # Now handle the case of updating an existing `.env` file.
    # To preserve formatting, multiline variables, and inline comments on
    # variable defintions, we re-use the parser used by `python_dotenv`.
    # It is not trivial to re-implement their parser.
    #
    # Algorithm overview:
    #
    # 1. The `parse_stream()` function returns an Iterator that yields 'Binding'
    # objects that represent 'parsed chunks' of a `.env` file. Each chunk may
    # contain:
    #
    # - An environment variable definition (`Binding.key is not None`),
    # - An invalid line (`Binding.error == True`),
    # - A standalone comment (if neither condition applies).
    #
    # 2. (Case 1) Invalid lines and environment variable bindings listed in
    # `secrets_to_remove` are ignored.
    #
    # 3. (Case 2) Environment variable definitions listed in `secrets_to_update`
    # are appended to `new_content` with the new value.
    #
    # 4. (Case 3) All other `Binding` objects are appended to `new_content` as-is.
    #
    # 5. Finally, new environment variables listed in `secrets_to_add` are
    # appended at the end after the `.env` file is fully parsed.
    new_content = ""
    for binding in parse_stream(StringIO(dotenv_content)):
        # Case 1
        if binding.error or binding.key in secrets_to_remove:
            continue
        # Case 2
        if binding.key in secrets_to_update:
            name = binding.key
            # extra logic to preserve formatting as best as we can
            whitespace_before, whitespace_after = get_whitespace_around(
                binding.original.string
            )
            value = secrets_to_update[name]
            new_content += whitespace_before
            new_content += f'{name}="{value}"'
            new_content += whitespace_after
            continue
        # Case 3
        new_content += binding.original.string

    if secrets_to_add:
        # Ensure new secrets get put at least 2 lines below the rest
        if not new_content.endswith("\n"):
            new_content += "\n\n"
        elif not new_content.endswith("\n\n"):
            new_content += "\n"

        max_i = len(secrets_to_add) - 1
        for i, (name, value) in enumerate(secrets_to_add.items()):
            new_content += f'{name}="{value}"\n'
            if i != max_i:
                new_content += "\n"

    return new_content


def get_whitespace_around(text: str) -> tuple[str, str]:
    """
    Extract whitespace prefix and suffix from a string.

    Args:
        text: The input string

    Returns:
        A tuple of (prefix, suffix) where prefix is the leading whitespace
        and suffix is the trailing whitespace
    """
    if not text:
        return ("", "")

    # Find prefix (leading whitespace)
    prefix_end = 0
    for i, char in enumerate(text):
        if not char.isspace():
            prefix_end = i
            break
    else:
        # String is all whitespace
        return (text, "")

    # Find suffix (trailing whitespace)
    suffix_start = len(text)
    for i in range(len(text) - 1, -1, -1):
        if not text[i].isspace():
            suffix_start = i + 1
            break

    prefix = text[:prefix_end]
    suffix = text[suffix_start:]

    return (prefix, suffix)
