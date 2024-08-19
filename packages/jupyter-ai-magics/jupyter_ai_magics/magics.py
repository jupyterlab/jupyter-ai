import base64
import json
import keyword
import os
import re
import sys
import warnings
from typing import Optional

import click
import traitlets
from IPython.core.magic import Magics, line_cell_magic, magics_class
from IPython.display import HTML, JSON, Markdown, Math
from jupyter_ai_magics.aliases import MODEL_ID_ALIASES
from jupyter_ai_magics.utils import decompose_model_id, get_lm_providers
from langchain.chains import LLMChain
from langchain.schema import HumanMessage

from ._version import __version__
from .parsers import (
    CellArgs,
    DeleteArgs,
    ErrorArgs,
    HelpArgs,
    ListArgs,
    RegisterArgs,
    UpdateArgs,
    VersionArgs,
    cell_magic_parser,
    line_magic_parser,
)
from .providers import BaseProvider


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

    aliases = traitlets.Dict(
        default_value=MODEL_ID_ALIASES,
        value_trait=traitlets.Unicode(),
        key_trait=traitlets.Unicode(),
        help="""Aliases for model identifiers.

        Keys define aliases, values define the provider and the model to use.
        The values should include identifiers in in the `provider:model` format.
        """,
        config=True,
    )

    default_language_model = traitlets.Unicode(
        default_value=None,
        allow_none=True,
        help="""Default language model to use, as string in the format
        <provider-id>:<model-id>, defaults to None.
        """,
        config=True,
    )

    def __init__(self, shell):
        super().__init__(shell)
        self.transcript_openai = []

        # suppress warning when using old Anthropic provider
        warnings.filterwarnings(
            "ignore",
            message="This Anthropic LLM is deprecated. Please use "
            "`from langchain.chat_models import ChatAnthropic` instead",
        )

        # suppress warning about our exception handler
        warnings.filterwarnings(
            "ignore",
            message="IPython detected, but you already "
            "have a custom exception handler installed. I'll skip installing "
            "Trio's custom handler, but this means exception groups will not "
            "show full tracebacks.",
        )

        self.providers = get_lm_providers()

        # initialize a registry of custom model/chain names
        self.custom_model_registry = self.aliases

    def _ai_bulleted_list_models_for_provider(self, provider_id, Provider):
        output = ""
        if len(Provider.models) == 1 and Provider.models[0] == "*":
            if Provider.help is None:
                output += f"* {PROVIDER_NO_MODELS}\n"
            else:
                output += f"* {Provider.help}\n"
        else:
            for model_id in Provider.models:
                output += f"* {provider_id}:{model_id}\n"
        output += "\n"  # End of bulleted list

        return output

    def _ai_inline_list_models_for_provider(self, provider_id, Provider):
        output = "<ul>"

        if len(Provider.models) == 1 and Provider.models[0] == "*":
            if Provider.help is None:
                return PROVIDER_NO_MODELS
            else:
                return Provider.help

        for model_id in Provider.models:
            output += f"<li>`{provider_id}:{model_id}`</li>"

        return output + "</ul>"

    # Is the required environment variable set?
    def _ai_env_status_for_provider_markdown(self, provider_id):
        na_message = "Not applicable. | " + NA_MESSAGE

        if (
            provider_id not in self.providers
            or self.providers[provider_id].auth_strategy == None
        ):
            return na_message  # No emoji

        not_set_title = ENV_NOT_SET
        set_title = ENV_SET
        env_status_ok = False

        auth_strategy = self.providers[provider_id].auth_strategy
        if auth_strategy.type == "env":
            var_name = auth_strategy.name
            env_var_display = f"`{var_name}`"
            env_status_ok = var_name in os.environ
        elif auth_strategy.type == "multienv":
            # Check multiple environment variables
            var_names = self.providers[provider_id].auth_strategy.names
            formatted_names = [f"`{name}`" for name in var_names]
            env_var_display = ", ".join(formatted_names)
            env_status_ok = all(var_name in os.environ for var_name in var_names)
            not_set_title = MULTIENV_NOT_SET
            set_title = MULTIENV_SET
        else:  # No environment variables
            return na_message

        output = f"{env_var_display} | "
        if env_status_ok:
            output += f'<abbr title="{set_title}">✅</abbr>'
        else:
            output += f'<abbr title="{not_set_title}">❌</abbr>'

        return output

    def _ai_env_status_for_provider_text(self, provider_id):
        # only handle providers with "env" or "multienv" auth strategy
        auth_strategy = getattr(self.providers[provider_id], "auth_strategy", None)
        if not auth_strategy or (
            auth_strategy.type != "env" and auth_strategy.type != "multienv"
        ):
            return ""

        prefix = ENV_REQUIRES if auth_strategy.type == "env" else MULTIENV_REQUIRES
        envvars = (
            [auth_strategy.name]
            if auth_strategy.type == "env"
            else auth_strategy.names[:]
        )

        for i in range(len(envvars)):
            envvars[i] += " (set)" if envvars[i] in os.environ else " (not set)"

        return prefix + " " + ", ".join(envvars) + "\n"

    # Is this a name of a Python variable that can be called as a LangChain chain?
    def _is_langchain_chain(self, name):
        # Reserved word in Python?
        if keyword.iskeyword(name):
            return False

        acceptable_name = re.compile("^[a-zA-Z0-9_]+$")
        if not acceptable_name.match(name):
            return False

        ipython = self.shell
        return name in ipython.user_ns and isinstance(ipython.user_ns[name], LLMChain)

    # Is this an acceptable name for an alias?
    def _validate_name(self, register_name):
        # A registry name contains ASCII letters, numbers, hyphens, underscores,
        # and periods. No other characters, including a colon, are permitted
        acceptable_name = re.compile("^[a-zA-Z0-9._-]+$")
        if not acceptable_name.match(register_name):
            raise ValueError(
                "A registry name may contain ASCII letters, numbers, hyphens, underscores, "
                + "and periods. No other characters, including a colon, are permitted"
            )

    # Initially set or update an alias to a target
    def _safely_set_target(self, register_name, target):
        # If target is a string, treat this as an alias to another model.
        if self._is_langchain_chain(target):
            ip = self.shell
            self.custom_model_registry[register_name] = ip.user_ns[target]
        else:
            # Ensure that the destination is properly formatted
            if ":" not in target:
                raise ValueError(
                    "Target model must be an LLMChain object or a model name in PROVIDER_ID:MODEL_NAME format"
                )

            self.custom_model_registry[register_name] = target

    def handle_delete(self, args: DeleteArgs):
        if args.name in AI_COMMANDS:
            raise ValueError(
                f"Reserved command names, including {args.name}, cannot be deleted"
            )

        if args.name not in self.custom_model_registry:
            raise ValueError(f"There is no alias called {args.name}")

        del self.custom_model_registry[args.name]
        output = f"Deleted alias `{args.name}`"
        return TextOrMarkdown(output, output)

    def handle_register(self, args: RegisterArgs):
        # Existing command names are not allowed
        if args.name in AI_COMMANDS:
            raise ValueError(f"The name {args.name} is reserved for a command")

        # Existing registered names are not allowed
        if args.name in self.custom_model_registry:
            raise ValueError(
                f"The name {args.name} is already associated with a custom model; "
                + "use %ai update to change its target"
            )

        # Does the new name match expected format?
        self._validate_name(args.name)

        self._safely_set_target(args.name, args.target)
        output = f"Registered new alias `{args.name}`"
        return TextOrMarkdown(output, output)

    def handle_update(self, args: UpdateArgs):
        if args.name in AI_COMMANDS:
            raise ValueError(
                f"Reserved command names, including {args.name}, cannot be updated"
            )

        if args.name not in self.custom_model_registry:
            raise ValueError(f"There is no alias called {args.name}")

        self._safely_set_target(args.name, args.target)
        output = f"Updated target of alias `{args.name}`"
        return TextOrMarkdown(output, output)

    def _ai_list_command_markdown(self, single_provider=None):
        output = (
            "| Provider | Environment variable | Set? | Models |\n"
            + "|----------|----------------------|------|--------|\n"
        )
        if single_provider is not None and single_provider not in self.providers:
            return f"There is no model provider with ID `{single_provider}`."

        for provider_id, Provider in self.providers.items():
            if single_provider is not None and provider_id != single_provider:
                continue

            output += (
                f"| `{provider_id}` | "
                + self._ai_env_status_for_provider_markdown(provider_id)
                + " | "
                + self._ai_inline_list_models_for_provider(provider_id, Provider)
                + " |\n"
            )

        # Also list aliases.
        if single_provider is None and len(self.custom_model_registry) > 0:
            output += (
                "\nAliases and custom commands:\n\n"
                + "| Name | Target |\n"
                + "|------|--------|\n"
            )
            for key, value in self.custom_model_registry.items():
                output += f"| `{key}` | "
                if isinstance(value, str):
                    output += f"`{value}`"
                else:
                    output += "*custom chain*"

                output += " |\n"

        return output

    def _ai_list_command_text(self, single_provider=None):
        output = ""
        if single_provider is not None and single_provider not in self.providers:
            return f"There is no model provider with ID '{single_provider}'."

        for provider_id, Provider in self.providers.items():
            if single_provider is not None and provider_id != single_provider:
                continue

            output += (
                f"{provider_id}\n"
                + self._ai_env_status_for_provider_text(
                    provider_id
                )  # includes \n if nonblank
                + self._ai_bulleted_list_models_for_provider(provider_id, Provider)
            )

        # Also list aliases.
        if single_provider is None and len(self.custom_model_registry) > 0:
            output += "\nAliases and custom commands:\n"
            for key, value in self.custom_model_registry.items():
                output += f"{key} - "
                if isinstance(value, str):
                    output += value
                else:
                    output += "custom chain"

                output += "\n"

        return output

    def handle_error(self, args: ErrorArgs):
        no_errors = "There have been no errors since the kernel started."

        # Find the most recent error.
        ip = self.shell
        if "Err" not in ip.user_ns:
            return TextOrMarkdown(no_errors, no_errors)

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
            return TextOrMarkdown(no_errors, no_errors)

        prompt = f"Explain the following error:\n\n{last_error}"
        # Set CellArgs based on ErrorArgs
        values = args.dict()
        values["type"] = "root"
        cell_args = CellArgs(**values)

        return self.run_ai_cell(cell_args, prompt)

    def _decompose_model_id(self, model_id: str):
        """Breaks down a model ID into a two-tuple (provider_id, local_model_id). Returns (None, None) if indeterminate."""
        # custom_model_registry maps keys to either a model name (a string) or an LLMChain.
        # If this is an alias to another model, expand the full name of the model.
        if model_id in self.custom_model_registry and isinstance(
            self.custom_model_registry[model_id], str
        ):
            model_id = self.custom_model_registry[model_id]

        return decompose_model_id(model_id, self.providers)

    def _get_provider(self, provider_id: Optional[str]) -> BaseProvider:
        """Returns the model provider ID and class for a model ID. Returns None if indeterminate."""
        if provider_id is None or provider_id not in self.providers:
            return None

        return self.providers[provider_id]

    def display_output(self, output, display_format, md):
        # build output display
        DisplayClass = DISPLAYS_BY_FORMAT[display_format]

        # if the user wants code, add another cell with the output.
        if display_format == "code":
            # Strip a leading language indicator and trailing triple-backticks
            lang_indicator = r"^```[a-zA-Z0-9]*\n"
            output = re.sub(lang_indicator, "", output)
            output = re.sub(r"\n```$", "", output)
            new_cell_payload = dict(
                source="set_next_input",
                text=output,
                replace=False,
            )
            ip = self.shell
            ip.payload_manager.write_payload(new_cell_payload)
            return HTML(
                "AI generated code inserted below &#11015;&#65039;", metadata=md
            )

        if DisplayClass is None:
            return output
        if display_format == "json":
            # JSON display expects a dict, not a JSON string
            output = json.loads(output)
        output_display = DisplayClass(output, metadata=md)

        # finally, display output display
        return output_display

    def handle_help(self, _: HelpArgs):
        # The line parser's help function prints both cell and line help
        with click.Context(line_magic_parser, info_name="%ai") as ctx:
            click.echo(line_magic_parser.get_help(ctx))

    def handle_list(self, args: ListArgs):
        return TextOrMarkdown(
            self._ai_list_command_text(args.provider_id),
            self._ai_list_command_markdown(args.provider_id),
        )

    def handle_version(self, args: VersionArgs):
        return __version__

    def run_ai_cell(self, args: CellArgs, prompt: str):
        provider_id, local_model_id = self._decompose_model_id(args.model_id)

        # If this is a custom chain, send the message to the custom chain.
        if args.model_id in self.custom_model_registry and isinstance(
            self.custom_model_registry[args.model_id], LLMChain
        ):
            # Get the output, either as raw text or as the contents of the 'text' key of a dict
            invoke_output = self.custom_model_registry[args.model_id].invoke(prompt)
            if isinstance(invoke_output, dict):
                invoke_output = invoke_output.get("text")

            return self.display_output(
                invoke_output,
                args.format,
                {"jupyter_ai": {"custom_chain_id": args.model_id}},
            )

        Provider = self._get_provider(provider_id)
        if Provider is None:
            return TextOrMarkdown(
                CANNOT_DETERMINE_MODEL_TEXT.format(args.model_id)
                + "\n\n"
                + "If you were trying to run a command, run '%ai help' to see a list of commands.",
                CANNOT_DETERMINE_MODEL_MARKDOWN.format(args.model_id)
                + "\n\n"
                + "If you were trying to run a command, run `%ai help` to see a list of commands.",
            )

        # validate presence of authn credentials
        auth_strategy = self.providers[provider_id].auth_strategy
        if auth_strategy:
            if auth_strategy.type == "env" and auth_strategy.name not in os.environ:
                raise OSError(
                    f"Authentication environment variable {auth_strategy.name} is not set.\n"
                    f"An authentication token is required to use models from the {Provider.name} provider.\n"
                    f"Please specify it via `%env {auth_strategy.name}=token`. "
                ) from None
            if auth_strategy.type == "multienv":
                # Multiple environment variables must be set
                missing_vars = [
                    var for var in auth_strategy.names if var not in os.environ
                ]
                raise OSError(
                    f"Authentication environment variables {missing_vars} are not set.\n"
                    f"Multiple authentication tokens are required to use models from the {Provider.name} provider.\n"
                    f"Please specify them all via `%env` commands. "
                ) from None

        # configure and instantiate provider
        provider_params = {"model_id": local_model_id}
        # for SageMaker, validate that required params are specified
        if provider_id == "sagemaker-endpoint":
            if (
                args.region_name is None
                or args.request_schema is None
                or args.response_path is None
            ):
                raise ValueError(
                    "When using the sagemaker-endpoint provider, you must specify all of "
                    + "the --region-name, --request-schema, and --response-path options."
                )
            provider_params["region_name"] = args.region_name
            provider_params["request_schema"] = args.request_schema
            provider_params["response_path"] = args.response_path

        model_parameters = json.loads(args.model_parameters)

        provider = Provider(**provider_params, **model_parameters)

        # Apply a prompt template.
        prompt = provider.get_prompt_template(args.format).format(prompt=prompt)

        # interpolate user namespace into prompt
        ip = self.shell
        prompt = prompt.format_map(FormatDict(ip.user_ns))

        if provider.is_chat_provider:
            result = provider.generate([[HumanMessage(content=prompt)]])
        else:
            # generate output from model via provider
            result = provider.generate([prompt])

        output = result.generations[0][0].text
        md = {"jupyter_ai": {"provider_id": provider_id, "model_id": local_model_id}}

        return self.display_output(output, args.format, md)

    @line_cell_magic
    def ai(self, line, cell=None):
        raw_args = line.split(" ")
        default_map = {"model_id": self.default_language_model}
        if cell:
            args = cell_magic_parser(
                raw_args,
                prog_name="%%ai",
                standalone_mode=False,
                default_map={"cell_magic_parser": default_map},
            )
        else:
            args = line_magic_parser(
                raw_args,
                prog_name="%ai",
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
        except ValueError as e:
            print(e, file=sys.stderr)
            return

        # hint to the IDE that this object must be of type `RootArgs`
        args: CellArgs = args

        if not cell:
            raise CellMagicError(
                """[0.8+]: To invoke a language model, you must use the `%%ai`
                cell magic. The `%ai` line magic is only for use with
                subcommands."""
            )

        prompt = cell.strip()

        # interpolate user namespace into prompt
        ip = self.shell
        prompt = prompt.format_map(FormatDict(ip.user_ns))

        return self.run_ai_cell(args, prompt)
