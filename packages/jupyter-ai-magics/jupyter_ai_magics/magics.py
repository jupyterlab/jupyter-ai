import base64
import json
import keyword
import os
import re
import sys
import warnings
from typing import Optional

import click
from IPython import get_ipython
from IPython.core.magic import Magics, line_cell_magic, magics_class
from IPython.display import HTML, JSON, Markdown, Math
from jupyter_ai_magics.utils import decompose_model_id, get_lm_providers
from langchain.chains import LLMChain
from langchain.schema import HumanMessage

from .parsers import (
    CellArgs,
    DeleteArgs,
    ErrorArgs,
    HelpArgs,
    ListArgs,
    RegisterArgs,
    UpdateArgs,
    cell_magic_parser,
    line_magic_parser,
)
from .providers import BaseProvider

MODEL_ID_ALIASES = {
    "gpt2": "huggingface_hub:gpt2",
    "gpt3": "openai:text-davinci-003",
    "chatgpt": "openai-chat:gpt-3.5-turbo",
    "gpt4": "openai-chat:gpt-4",
    "titan": "bedrock:amazon.titan-tg1-large",
}


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

MARKDOWN_PROMPT_TEMPLATE = "{prompt}\n\nProduce output in markdown format only."

PROVIDER_NO_MODELS = "This provider does not define a list of models."

CANNOT_DETERMINE_MODEL_TEXT = """Cannot determine model provider from model ID '{0}'.

To see a list of models you can use, run '%ai list'"""

CANNOT_DETERMINE_MODEL_MARKDOWN = """Cannot determine model provider from model ID `{0}`.

To see a list of models you can use, run `%ai list`"""


PROMPT_TEMPLATES_BY_FORMAT = {
    "code": "{prompt}\n\nProduce output as source code only, with no text or explanation before or after it.",
    "html": "{prompt}\n\nProduce output in HTML format only, with no markup before or afterward.",
    "image": "{prompt}\n\nProduce output as an image only, with no text before or after it.",
    "markdown": MARKDOWN_PROMPT_TEMPLATE,
    "md": MARKDOWN_PROMPT_TEMPLATE,
    "math": "{prompt}\n\nProduce output in LaTeX format only, with $$ at the beginning and end.",
    "json": "{prompt}\n\nProduce output in JSON format only, with nothing before or after it.",
    "text": "{prompt}",  # No customization
}

AI_COMMANDS = {"delete", "error", "help", "list", "register", "update"}


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
    def __init__(self, shell):
        super().__init__(shell)
        self.transcript_openai = []

        # suppress warning when using old OpenAIChat provider
        warnings.filterwarnings(
            "ignore",
            message="You are trying to use a chat model. This way of initializing it is "
            "no longer supported. Instead, please use: "
            "`from langchain.chat_models import ChatOpenAI`",
        )
        # suppress warning when using old Anthropic provider
        warnings.filterwarnings(
            "ignore",
            message="This Anthropic LLM is deprecated. Please use "
            "`from langchain.chat_models import ChatAnthropic` instead",
        )

        self.providers = get_lm_providers()

        # initialize a registry of custom model/chain names
        self.custom_model_registry = MODEL_ID_ALIASES

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
        output = ""

        if len(Provider.models) == 1 and Provider.models[0] == "*":
            if Provider.help is None:
                return PROVIDER_NO_MODELS
            else:
                return Provider.help

        for model_id in Provider.models:
            output += f", `{provider_id}:{model_id}`"

        # Remove initial comma
        return re.sub(r"^, ", "", output)

    # Is the required environment variable set?
    def _ai_env_status_for_provider_markdown(self, provider_id):
        na_message = "Not applicable. | " + NA_MESSAGE

        if (
            provider_id not in self.providers
            or self.providers[provider_id].auth_strategy == None
        ):
            return na_message  # No emoji

        try:
            env_var = self.providers[provider_id].auth_strategy.name
        except AttributeError:  # No "name" attribute
            return na_message

        output = f"`{env_var}` | "
        if os.getenv(env_var) == None:
            output += (
                '<abbr title="You have not set this environment variable, '
                + "so you cannot use this provider's models.\">❌</abbr>"
            )
        else:
            output += (
                '<abbr title="You have set this environment variable, '
                + "so you can use this provider's models.\">✅</abbr>"
            )

        return output

    def _ai_env_status_for_provider_text(self, provider_id):
        if (
            provider_id not in self.providers
            or self.providers[provider_id].auth_strategy == None
        ):
            return ""  # No message necessary

        try:
            env_var = self.providers[provider_id].auth_strategy.name
        except AttributeError:  # No "name" attribute
            return ""

        output = f"Requires environment variable {env_var} "
        if os.getenv(env_var) != None:
            output += "(set)"
        else:
            output += "(not set)"

        return output + "\n"

    # Is this a name of a Python variable that can be called as a LangChain chain?
    def _is_langchain_chain(self, name):
        # Reserved word in Python?
        if keyword.iskeyword(name):
            return False

        acceptable_name = re.compile("^[a-zA-Z0-9_]+$")
        if not acceptable_name.match(name):
            return False

        ipython = get_ipython()
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
            ip = get_ipython()
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
        ip = get_ipython()
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
        cell_args = CellArgs(
            type="root", model_id=args.model_id, format=args.format, reset=False
        )
        return self.run_ai_cell(cell_args, prompt)

    def _append_exchange_openai(self, prompt: str, output: str):
        """Appends a conversational exchange between user and an OpenAI Chat
        model to a transcript that will be included in future exchanges."""
        self.transcript_openai.append({"role": "user", "content": prompt})
        self.transcript_openai.append({"role": "assistant", "content": output})

    def _decompose_model_id(self, model_id: str):
        """Breaks down a model ID into a two-tuple (provider_id, local_model_id). Returns (None, None) if indeterminate."""
        if model_id in self.custom_model_registry:
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
            ip = get_ipython()
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

    def run_ai_cell(self, args: CellArgs, prompt: str):
        # Apply a prompt template.
        prompt = PROMPT_TEMPLATES_BY_FORMAT[args.format].format(prompt=prompt)

        # interpolate user namespace into prompt
        ip = get_ipython()
        prompt = prompt.format_map(FormatDict(ip.user_ns))

        # Determine provider and local model IDs
        # If this is a custom chain, send the message to the custom chain.
        if args.model_id in self.custom_model_registry and isinstance(
            self.custom_model_registry[args.model_id], LLMChain
        ):
            return self.display_output(
                self.custom_model_registry[args.model_id].run(prompt),
                args.format,
                {"jupyter_ai": {"custom_chain_id": args.model_id}},
            )

        provider_id, local_model_id = self._decompose_model_id(args.model_id)
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

        # if `--reset` is specified, reset transcript and return early
        if provider_id == "openai-chat" and args.reset:
            self.transcript_openai = []
            return

        # validate presence of authn credentials
        auth_strategy = self.providers[provider_id].auth_strategy
        if auth_strategy:
            # TODO: handle auth strategies besides EnvAuthStrategy
            if auth_strategy.type == "env" and auth_strategy.name not in os.environ:
                raise OSError(
                    f"Authentication environment variable {auth_strategy.name} not provided.\n"
                    f"An authentication token is required to use models from the {Provider.name} provider.\n"
                    f"Please specify it via `%env {auth_strategy.name}=token`. "
                ) from None

        # configure and instantiate provider
        provider_params = {"model_id": local_model_id}
        if provider_id == "openai-chat":
            provider_params["prefix_messages"] = self.transcript_openai
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

            # Validate that the request schema is well-formed JSON
            try:
                json.loads(args.request_schema)
            except json.JSONDecodeError as e:
                raise ValueError(
                    "request-schema must be valid JSON. "
                    f"Error at line {e.lineno}, column {e.colno}: {e.msg}"
                ) from None

        provider = Provider(**provider_params)

        # Apply a prompt template.
        prompt = provider.get_prompt_template(args.format).format(prompt=prompt)

        # interpolate user namespace into prompt
        ip = get_ipython()
        prompt = prompt.format_map(FormatDict(ip.user_ns))

        if provider.is_chat_provider:
            result = provider.generate([[HumanMessage(content=prompt)]])
        else:
            # generate output from model via provider
            result = provider.generate([prompt])

        output = result.generations[0][0].text

        # if openai-chat, append exchange to transcript
        if provider_id == "openai-chat":
            self._append_exchange_openai(prompt, output)

        md = {"jupyter_ai": {"provider_id": provider_id, "model_id": local_model_id}}

        return self.display_output(output, args.format, md)

    @line_cell_magic
    def ai(self, line, cell=None):
        raw_args = line.split(" ")
        if cell:
            args = cell_magic_parser(raw_args, prog_name="%%ai", standalone_mode=False)
        else:
            args = line_magic_parser(raw_args, prog_name="%ai", standalone_mode=False)

        if args == 0:
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
        ip = get_ipython()
        prompt = prompt.format_map(FormatDict(ip.user_ns))

        return self.run_ai_cell(args, prompt)
