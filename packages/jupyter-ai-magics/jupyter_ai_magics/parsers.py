import click
from pydantic import BaseModel
from typing import Optional, Literal, get_args

FORMAT_CHOICES_TYPE = Literal["code", "html", "image", "json", "markdown", "math", "md", "text"]
FORMAT_CHOICES = list(get_args(FORMAT_CHOICES_TYPE))

class CellArgs(BaseModel):
    type: Literal["root"] = "root"
    model_id: str
    format: FORMAT_CHOICES_TYPE
    reset: bool

class HelpArgs(BaseModel):
    type: Literal["help"] = "help"

class ListArgs(BaseModel):
    type: Literal["list"] = "list"
    provider_id: Optional[str]

class LineMagicGroup(click.Group):
    """Helper class to print the help string for cell magics as well when
    `%ai --help` is called."""
    def get_help(self, ctx):
        with click.Context(cell_magic_parser, info_name="%%ai") as ctx:
            click.echo(cell_magic_parser.get_help(ctx))
        click.echo('-' * 78)
        with click.Context(line_magic_parser, info_name="%ai") as ctx:
            click.echo(super().get_help(ctx))

@click.command()
@click.argument('model_id')
@click.option('-f', '--format',
    type=click.Choice(FORMAT_CHOICES, case_sensitive=False),
    default="markdown",
    help="""IPython display to use when rendering output. [default="markdown"]"""
)
@click.option('-r', '--reset', is_flag=True,
    help="""Clears the conversation transcript used when interacting with an
    OpenAI chat model provider. Does nothing with other providers."""
)
def cell_magic_parser(**kwargs):
    """
    Invokes a language model identified by MODEL_ID, with the prompt being
    contained in all lines after the first. Both local model IDs and global
    model IDs (with the provider ID explicitly prefixed, followed by a colon)
    are accepted.

    To view available language models, please run `%ai list`.
    """
    return CellArgs(**kwargs)

@click.group(cls=LineMagicGroup)
def line_magic_parser():
    """
    Invokes a subcommand.
    """

@line_magic_parser.command(name='help')
def help_subparser():
    """Show this message and exit."""
    return HelpArgs()

@line_magic_parser.command(name='list',
    short_help="List language models. See `%ai list --help` for options."
)
@click.argument('provider_id', required=False)
def list_subparser(**kwargs):
    """List language models, optionally scoped to PROVIDER_ID."""
    return ListArgs(**kwargs)
