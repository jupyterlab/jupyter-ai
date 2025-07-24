import base64
import json
import re
import sys
import warnings

import click
import traitlets
from IPython.core.magic import Magics, line_cell_magic, magics_class
from IPython.display import HTML, JSON, Markdown, Math

from ._version import __version__
from .parsers import (
    CellArgs,
    DeleteArgs,
    ErrorArgs,
    HelpArgs,
    ListArgs,
    RegisterArgs,
    ResetArgs,
    UpdateArgs,
    VersionArgs,
    cell_magic_parser,
    line_magic_parser,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

class TextOrMarkdown:
    def __init__(self, text, markdown):
        self.text = text
        self.markdown = markdown

    def _repr_mimebundle_(self, include=None, exclude=None):
        return {"text/plain": self.text, "text/markdown": self.markdown}


class TextWithMetadata:
    def __init__(self, text, metadata):
        self.text = text
        self.metadata = metadata

    def __str__(self):
        return self.text

    def _repr_mimebundle_(self, include=None, exclude=None):
        return ({"text/plain": self.text}, self.metadata)


class Base64Image:
    def __init__(self, mimeData, metadata):
        mimeDataParts = mimeData.split(",")
        self.data = base64.b64decode(mimeDataParts[1])
        self.mimeType = re.sub(r";base64$", "", mimeDataParts[0])
        self.metadata = metadata

    def _repr_mimebundle_(self, include=None, exclude=None):
        return ({self.mimeType: self.data}, self.metadata)


DISPLAYS_BY_FORMAT = {
    "code": None,
    "html": HTML,
    "image": Base64Image,
    "markdown": Markdown,
    "math": Math,
    "md": Markdown,
    "json": JSON,
    "text": TextWithMetadata,
}

NA_MESSAGE = '<abbr title="Not applicable">N/A</abbr>'

PROVIDER_NO_MODELS = "This provider does not define a list of models."

CANNOT_DETERMINE_MODEL_TEXT = """Cannot determine model provider from model ID '{0}'.

To see a list of models you can use, run '%ai list'"""

CANNOT_DETERMINE_MODEL_MARKDOWN = """Cannot determine model provider from model ID `{0}`.

To see a list of models you can use, run `%ai list`"""


AI_COMMANDS = {"delete", "error", "help", "list", "register", "update"}

# Strings for listing providers and models
# Avoid composing strings, to make localization easier in the future
ENV_NOT_SET = "You have not set this environment variable, so you cannot use this provider's models."
ENV_SET = (
    "You have set this environment variable, so you can use this provider's models."
)
MULTIENV_NOT_SET = "You have not set all of these environment variables, so you cannot use this provider's models."
MULTIENV_SET = "You have set all of these environment variables, so you can use this provider's models."

ENV_REQUIRES = "Requires environment variable:"
MULTIENV_REQUIRES = "Requires environment variables:"


class FormatDict(dict):
    """Subclass of dict to be passed to str#format(). Suppresses KeyError and
    leaves replacement field unchanged if replacement field is not associated
    with a value."""

    def __missing__(self, key):
        return key.join("{}")


class EnvironmentError(BaseException):
    pass


class CellMagicError(BaseException):
    pass


@magics_class
class AiMagics(Magics):

    # TODO: rename this to initial_aliases
    # This should only set the "starting set" of aliases
    aliases = traitlets.Dict(
        default_value={},
        value_trait=traitlets.Unicode(),
        key_trait=traitlets.Unicode(),
        help="""Aliases for model identifiers.

        Keys define aliases, values define the provider and the model to use.
        The values should include identifiers in in the `provider:model` format.
        """,
        config=True,
    )

    # TODO: rename this to initial_language_model
    default_language_model = traitlets.Unicode(
        default_value=None,
        allow_none=True,
        help="""Default language model to use, as string in the format
        <provider-id>:<model-id>, defaults to None.
        """,
        config=True,
    )

    max_history = traitlets.Int(
        default_value=2,
        allow_none=False,
        help="""Maximum number of exchanges (user/assistant) to include in the history
        when invoking a chat model, defaults to 2.
        """,
        config=True,
    )

    transcript: list[dict[str, str]]
    """
    The conversation history as a list of messages. Each message is a simple
    dictionary with the following structure:

    - `"role"`: `"user"`, `"assistant"`, or `"system"`
    - `"content"`: the content of the message
    """

    def __init__(self, shell):
        super().__init__(shell)
        self.transcript = []

        # TODO: check if this is necessary
        # suppress warning about our exception handler
        warnings.filterwarnings(
            "ignore",
            message="IPython detected, but you already "
            "have a custom exception handler installed. I'll skip installing "
            "Trio's custom handler, but this means exception groups will not "
            "show full tracebacks.",
        )

        # TODO: use LiteLLM aliases to provide this
        # https://docs.litellm.ai/docs/completion/model_alias
        # initialize a registry of custom model/chain names
        self.custom_model_registry = self.aliases

    @line_cell_magic
    def ai(self, line: str, cell: Optional[str] = None) -> Any:
        """
        Defines how `%ai` and `%%ai` magic commands are handled. This is called
        first whenever either `%ai` or `%%ai` is run, so it should be considered
        the main method of the `AiMagics` class.

        - `%ai` is a "line magic command" that only accepts a single line of
        input. This is used to provide access to sub-commands like `%ai
        register`.

        - `%%ai` is a "cell magic command" that accepts an entire cell of input
        (i.e. multiple lines). This is used to invoke a language model.

        This method is called when either `%ai` or `%%ai` is run. Whether a line
        or cell magic was run can be determined by the arguments given to this
        method; `%%ai` was run if and only if `cell is not None`.
        """
        raw_args = line.split(" ")
        default_map = {"model_id": self.default_language_model}

        # parse arguments
        if cell:
            args = cell_magic_parser(
                raw_args,
                prog_name=r"%%ai",
                standalone_mode=False,
                default_map={"cell_magic_parser": default_map},
            )
        else:
            args = line_magic_parser(
                raw_args,
                prog_name=r"%ai",
                standalone_mode=False,
                default_map={"error": default_map},
            )

        if args == 0 and self.default_language_model is None:
            # this happens when `--help` is called on the root command, in which
            # case we want to exit early.
            return

        # If a value error occurs, don't print the full stacktrace
        try:
            if args.type == "error":
                return self.handle_error(args)
            if args.type == "help":
                return self.handle_help(args)
            if args.type == "list":
                return self.handle_list(args)
            if args.type == "register":
                return self.handle_register(args)
            if args.type == "delete":
                return self.handle_delete(args)
            if args.type == "update":
                return self.handle_update(args)
            if args.type == "version":
                return self.handle_version(args)
            if args.type == "reset":
                return self.handle_reset(args)
        except ValueError as e:
            print(e, file=sys.stderr)
            return

        # hint to the IDE that this object must be of type `CellArgs`
        args: CellArgs = args

        if not cell:
            raise CellMagicError(
                """To invoke a language model, you must use the `%%ai`
                cell magic. The `%ai` line magic is only for use with
                subcommands."""
            )

        prompt = cell.strip()

        return self.run_ai_cell(args, prompt)

    def run_ai_cell(self, args: CellArgs, prompt: str):
        """
        Handles the `%%ai` cell magic. This is the main method that invokes the
        language model.
        """
        # Apply a prompt template.
        # The LLM needs to be given instructions based on `args.format`. See
        # `old_prompt_templates.txt`.
        #
        # We may want to drop some of these formats for simplicity, since they
        # don't all seem that helpful.
        #
        # TODO
        prompt = prompt

        # Interpolate local variables into prompt.
        # For example, if a user runs `a = "hello"` and then runs `%%ai {a}`, it
        # should be equivalent to running `%%ai hello`.
        ip = self.shell
        prompt = prompt.format_map(FormatDict(ip.user_ns))

        # TODO: generate the output using LiteLLM
        # include `self.transcript` for conversation history
        user_message = {
            "role": "user",
            "content": prompt
        }
        # ... call litellm.acompletion(<model-id>, [*self.transcript, user_message])
        # store response as a string in `output`
        output: str = "TODO"

        # append exchange to transcript
        self._append_exchange(prompt, output)

        # TODO: set model ID in metadata 
        metadata = {"jupyter_ai_v3": {"model_id": "TODO"}}

        # Return output given the format
        return self.display_output(output, args.format, metadata)

    def display_output(self, output, display_format, metadata: Dict[str, Any]) -> Any:
        """
        Returns an IPython 'display object' that determines how an output is
        rendered. This is complex, so here are some notes:

        - The display object returned is controlled by the `display_format`
        argument. See `DISPLAYS_BY_FORMAT` for the list of valid formats.

        - In most use-cases, this method returns a `TextOrMarkdown` object. The
        reason this exists is because IPython may be run from a terminal shell
        (via the `ipython` command) or from a web browser in a Jupyter Notebook.

        - `TextOrMarkdown` shows text when viewed from a command line, and rendered
        Markdown when viewed from a web browser.

        - See `DISPLAYS_BY_FORMAT` for the list of display objects that can be
        returned by `jupyter_ai_magics`. 

        TODO: Use a string enum to store the list of valid formats.

        TODO: What is the shared type that all display objects implement? We
        implement `_repr_mime_()` but that doesn't seem to be implemented on all
        display objects. So the return type is `Any` for now.
        """
        # build output display
        DisplayClass = DISPLAYS_BY_FORMAT[display_format]

        # if the user wants code, add another cell with the output.
        if display_format == "code":
            # Strip a leading language indicator and trailing triple-backticks
            lang_indicator = r"^```[a-zA-Z0-9]*\n"
            output = re.sub(lang_indicator, "", output)
            output = re.sub(r"\n```$", "", output)
            self.shell.set_next_input(output, replace=False)
            return HTML(
                "AI generated code inserted below &#11015;&#65039;", metadata=metadata
            )

        if DisplayClass is None:
            return output
        if display_format == "json":
            # JSON display expects a dict, not a JSON string
            output = json.loads(output)
        output_display = DisplayClass(output, metadata=metadata)

        # finally, display output display
        return output_display

    def _append_exchange(self, prompt: str, output: str):
        """
        Appends an exchange between a user and a language model to
        `self.transcript`. This transcript will be included in future `%ai`
        calls to preserve conversation history.

        TODO: bound this list to length `self.max_history * 2`.
        """
        self.transcript.append({
            "role": "user",
            "content": prompt
        })
        self.transcript.append({
            "role": "assistant",
            "content": output
        })

    def handle_help(self, _: HelpArgs) -> None:
        """
        Handles `%ai help`. Prints a help message via `click.echo()`.
        """
        # The line parser's help function prints both cell and line help
        with click.Context(line_magic_parser, info_name=r"%ai") as ctx:
            click.echo(line_magic_parser.get_help(ctx))


    def handle_delete(self, args: DeleteArgs) -> TextOrMarkdown:
        """
        Handles `%ai delete`. Deletes a model alias.

        TODO: rename the command to `%ai dealias`?
        """

        if args.name in AI_COMMANDS:
            raise ValueError(
                f"Reserved command names, including {args.name}, cannot be deleted"
            )

        if args.name not in self.custom_model_registry:
            raise ValueError(f"There is no alias called {args.name}")

        del self.custom_model_registry[args.name]
        output = f"Deleted alias `{args.name}`"
        return TextOrMarkdown(output, output)

    def handle_reset(self, args: ResetArgs) -> None:
        """
        Handles `%ai reset`. Clears the history.
        """
        self.transcript = []

    def handle_error(self, args: ErrorArgs) -> Any:
        """
        Handles `%ai error`. Meant to provide fixes for any exceptions raised in
        the kernel while running cells.

        TODO: rename this to `%ai fix`?

        TODO: annotate a valid return type when we find a type that is shared by
        all display objects.
        """
        no_errors_message = "There have been no errors since the kernel started."

        # Find the most recent error.
        ip = self.shell
        if "Err" not in ip.user_ns:
            return TextOrMarkdown(no_errors_message, no_errors_message)

        err = ip.user_ns["Err"]
        # Start from the previous execution count
        excount = ip.execution_count - 1
        last_error = None
        while excount >= 0 and last_error is None:
            if excount in err:
                last_error = err[excount]
            else:
                excount = excount - 1

        if last_error is None:
            return TextOrMarkdown(no_errors_message, no_errors_message)

        prompt = f"Explain the following error:\n\n{last_error}"
        # Set CellArgs based on ErrorArgs
        values = args.model_dump()
        values["type"] = "root"
        cell_args = CellArgs(**values)

        return self.run_ai_cell(cell_args, prompt)

    def handle_register(self, args: RegisterArgs) -> TextOrMarkdown:
        """
        Handles `%ai register`. Adds an alias for a model ID for future calls.

        TODO: Use LiteLLM to manage aliases. See
        https://docs.litellm.ai/docs/completion/model_alias

        TODO: rename this to `%ai alias`?
        """
        pass

    def handle_update(self, args: UpdateArgs) -> TextOrMarkdown:
        """
        Handles `%ai update`. Updates a model alias.

        TODO: remove this command. Users can just delete a model alias and add a
        new one.
        """
        pass

    def handle_version(self, args: VersionArgs) -> str:
        """
        Handles `%ai version`. Returns the current version of
        `jupyter_ai_magics`.
        """
        return __version__

    def handle_list(self, args: ListArgs):
        """
        Handles `%ai list`. Lists all LiteLLM models.

        The old implementation has been deleted because it was far too complex.

        TODO
        """
        pass
