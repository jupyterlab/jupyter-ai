import json
from typing import Literal, Optional, get_args

import click
from langchain.pydantic_v1 import BaseModel

FORMAT_CHOICES_TYPE = Literal[
    "code", "html", "image", "json", "markdown", "math", "md", "text"
]
FORMAT_CHOICES = list(get_args(FORMAT_CHOICES_TYPE))
FORMAT_HELP = """IPython display to use when rendering output. [default="markdown"]"""

REGION_NAME_SHORT_OPTION = "-n"
REGION_NAME_LONG_OPTION = "--region-name"
REGION_NAME_HELP = (
    "AWS region name, e.g. 'us-east-1'. Required for SageMaker provider; "
    + "does nothing with other providers."
)

REQUEST_SCHEMA_SHORT_OPTION = "-q"
REQUEST_SCHEMA_LONG_OPTION = "--request-schema"
REQUEST_SCHEMA_HELP = (
    "The JSON object the endpoint expects, with the prompt being "
    + "substituted into any value that matches the string literal '<prompt>'. "
    + "Required for SageMaker provider; does nothing with other providers."
)

RESPONSE_PATH_SHORT_OPTION = "-p"
RESPONSE_PATH_LONG_OPTION = "--response-path"
RESPONSE_PATH_HELP = (
    "A JSONPath string that retrieves the language model's output "
    + "from the endpoint's JSON response. Required for SageMaker provider; "
    + "does nothing with other providers."
)

MODEL_PARAMETERS_SHORT_OPTION = "-m"
MODEL_PARAMETERS_LONG_OPTION = "--model-parameters"
MODEL_PARAMETERS_HELP = (
    "A JSON value that specifies extra values that will be passed "
    "to the model. The accepted value parsed to a dict, unpacked "
    "and passed as-is to the provider class."
)


class CellArgs(BaseModel):
    type: Literal["root"] = "root"
    model_id: str
    format: FORMAT_CHOICES_TYPE
    model_parameters: Optional[str]
    # The following parameters are required only for SageMaker models
    region_name: Optional[str]
    request_schema: Optional[str]
    response_path: Optional[str]


# Should match CellArgs
class ErrorArgs(BaseModel):
    type: Literal["error"] = "error"
    model_id: str
    format: FORMAT_CHOICES_TYPE
    model_parameters: Optional[str]
    # The following parameters are required only for SageMaker models
    region_name: Optional[str]
    request_schema: Optional[str]
    response_path: Optional[str]


class HelpArgs(BaseModel):
    type: Literal["help"] = "help"


class VersionArgs(BaseModel):
    type: Literal["version"] = "version"


class ListArgs(BaseModel):
    type: Literal["list"] = "list"
    provider_id: Optional[str]


class RegisterArgs(BaseModel):
    type: Literal["register"] = "register"
    name: str
    target: str


class DeleteArgs(BaseModel):
    type: Literal["delete"] = "delete"
    name: str


class UpdateArgs(BaseModel):
    type: Literal["update"] = "update"
    name: str
    target: str


class LineMagicGroup(click.Group):
    """Helper class to print the help string for cell magics as well when
    `%ai --help` is called."""

    def get_help(self, ctx):
        with click.Context(cell_magic_parser, info_name="%%ai") as ctx:
            click.echo(cell_magic_parser.get_help(ctx))
        click.echo("-" * 78)
        with click.Context(line_magic_parser, info_name="%ai") as ctx:
            click.echo(super().get_help(ctx))


def verify_json_value(ctx, param, value):
    if not value:
        return value
    try:
        json.loads(value)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"{param.get_error_hint(ctx)} must be valid JSON. "
            f"Error at line {e.lineno}, column {e.colno}: {e.msg}"
        )
    return value


@click.command()
@click.argument("model_id", required=False)
@click.option(
    "-f",
    "--format",
    type=click.Choice(FORMAT_CHOICES, case_sensitive=False),
    default="markdown",
    help=FORMAT_HELP,
)
@click.option(
    REGION_NAME_SHORT_OPTION,
    REGION_NAME_LONG_OPTION,
    required=False,
    help=REGION_NAME_HELP,
)
@click.option(
    REQUEST_SCHEMA_SHORT_OPTION,
    REQUEST_SCHEMA_LONG_OPTION,
    required=False,
    help=REQUEST_SCHEMA_HELP,
    callback=verify_json_value,
)
@click.option(
    RESPONSE_PATH_SHORT_OPTION,
    RESPONSE_PATH_LONG_OPTION,
    required=False,
    help=RESPONSE_PATH_HELP,
)
@click.option(
    MODEL_PARAMETERS_SHORT_OPTION,
    MODEL_PARAMETERS_LONG_OPTION,
    required=False,
    help=MODEL_PARAMETERS_HELP,
    callback=verify_json_value,
    default="{}",
)
@click.pass_context
def cell_magic_parser(context: click.Context, **kwargs):
    """
    Invokes a language model identified by MODEL_ID, with the prompt being
    contained in all lines after the first. Both local model IDs and global
    model IDs (with the provider ID explicitly prefixed, followed by a colon)
    are accepted.

    To view available language models, please run `%ai list`.
    """
    if not kwargs["model_id"] and context.default_map:
        kwargs["model_id"] = context.default_map["cell_magic_parser"]["model_id"]
    return CellArgs(**kwargs)


@click.group(cls=LineMagicGroup)
def line_magic_parser():
    """
    Invokes a subcommand.
    """


@line_magic_parser.command(name="error")
@click.argument("model_id", required=False)
@click.option(
    "-f",
    "--format",
    type=click.Choice(FORMAT_CHOICES, case_sensitive=False),
    default="markdown",
    help=FORMAT_HELP,
)
@click.option(
    REGION_NAME_SHORT_OPTION,
    REGION_NAME_LONG_OPTION,
    required=False,
    help=REGION_NAME_HELP,
)
@click.option(
    REQUEST_SCHEMA_SHORT_OPTION,
    REQUEST_SCHEMA_LONG_OPTION,
    required=False,
    help=REQUEST_SCHEMA_HELP,
    callback=verify_json_value,
)
@click.option(
    RESPONSE_PATH_SHORT_OPTION,
    RESPONSE_PATH_LONG_OPTION,
    required=False,
    help=RESPONSE_PATH_HELP,
)
@click.option(
    MODEL_PARAMETERS_SHORT_OPTION,
    MODEL_PARAMETERS_LONG_OPTION,
    required=False,
    help=MODEL_PARAMETERS_HELP,
    callback=verify_json_value,
    default="{}",
)
@click.pass_context
def error_subparser(context: click.Context, **kwargs):
    """
    Explains the most recent error. Takes the same options (except -r) as
    the basic `%%ai` command.
    """
    if not kwargs["model_id"] and context.default_map:
        kwargs["model_id"] = context.default_map["error_subparser"]["model_id"]
    return ErrorArgs(**kwargs)


@line_magic_parser.command(name="version")
def version_subparser(**kwargs):
    """
    Prints Jupyter-AI version
    """
    return VersionArgs(**kwargs)


@line_magic_parser.command(name="help")
def help_subparser():
    """Show this message and exit."""
    return HelpArgs()


@line_magic_parser.command(
    name="list", short_help="List language models. See `%ai list --help` for options."
)
@click.argument("provider_id", required=False)
def list_subparser(**kwargs):
    """List language models, optionally scoped to PROVIDER_ID."""
    return ListArgs(**kwargs)


@line_magic_parser.command(
    name="register",
    short_help="Register a new alias. See `%ai register --help` for options.",
)
@click.argument("name")
@click.argument("target")
def register_subparser(**kwargs):
    """Register a new alias called NAME for the model or chain named TARGET."""
    return RegisterArgs(**kwargs)


@line_magic_parser.command(
    name="delete", short_help="Delete an alias. See `%ai delete --help` for options."
)
@click.argument("name")
def register_subparser(**kwargs):
    """Delete an alias called NAME."""
    return DeleteArgs(**kwargs)


@line_magic_parser.command(
    name="update",
    short_help="Update the target of an alias. See `%ai update --help` for options.",
)
@click.argument("name")
@click.argument("target")
def register_subparser(**kwargs):
    """Update an alias called NAME to refer to the model or chain named TARGET."""
    return UpdateArgs(**kwargs)
