import base64
import json
import os
import re
import sys
import warnings
import traceback
from typing import Any, Optional

import click
import litellm
import traitlets
from dotenv import load_dotenv
from IPython.core.magic import Magics, line_cell_magic, magics_class
from IPython.display import HTML, JSON, Markdown, Math
from jupyter_ai.model_providers.model_list import CHAT_MODELS

from ._version import __version__
from .parsers import (
    CellArgs,
    DeleteArgs,
    FixArgs,
    HelpArgs,
    ListArgs,
    RegisterArgs,
    ResetArgs,
    UpdateArgs,
    VersionArgs,
    cell_magic_parser,
    line_magic_parser,
)
# Test 20251116 Start
import nbformat as nbf
# import ipynbname as ipn
# Test 20251116 End

# Load the .env file from the workspace root
dotenv_path = os.path.join(os.getcwd(), ".env")


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


AI_COMMANDS = {"dealias", "fix", "help", "list", "alias", "update"}

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
    initial_aliases = traitlets.Dict(
        default_value={},
        value_trait=traitlets.Dict(),
        key_trait=traitlets.Unicode(),
        help="""Aliases for model identifiers.

        Keys define aliases, values define a dictionary containing:
        - target: The provider and model to use in the `provider:model` format
        - api_base: Optional base URL for the API endpoint
        - api_key_name: Optional name of the environment variable containing the API key
        """,
        config=True,
    )

    initial_language_model = traitlets.Unicode(
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

        # Notify if .env file is missing in workspace root when the extension is loaded.
        # This is useful for users to know that they can set API keys in the JupyterLab
        # UI, but it is not always required to run the extension.
        if not os.path.isfile(dotenv_path):
            print(
                f"No `.env` file containing provider API keys found at {dotenv_path}. \
                  You can add API keys to the `.env` file via the AI Settings in the JupyterLab UI.",
                file=sys.stderr,
            )

        # TODO: use LiteLLM aliases to provide this
        # https://docs.litellm.ai/docs/completion/model_alias
        # initialize a registry of custom model/chain names
        self.aliases = self.initial_aliases.copy()

    @line_cell_magic
    def ai(self, line: str, cell: Optional[str] = None) -> Any:
        """
        Defines how `%ai` and `%%ai` magic commands are handled. This is called
        first whenever either `%ai` or `%%ai` is run, so it should be considered
        the main method of the `AiMagics` class.

        - `%ai` is a "line magic command" that only accepts a single line of
        input. This is used to provide access to sub-commands like `%ai
        alias`.

        - `%%ai` is a "cell magic command" that accepts an entire cell of input
        (i.e. multiple lines). This is used to invoke a language model.

        This method is called when either `%ai` or `%%ai` is run. Whether a line
        or cell magic was run can be determined by the arguments given to this
        method; `%%ai` was run if and only if `cell is not None`.
        """
        # Load .env file from workspace root, with override=True in case `.env` has been modified
        # since the kernel started. This allows users to change API keys without restarting the kernel.
        if os.path.isfile(dotenv_path):
            load_dotenv(dotenv_path, override=True)

        raw_args = line.split(" ")
        default_map = {"model_id": self.initial_language_model}

        # parse arguments
        args = None
        try:
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
                    default_map={"fix": default_map},
                )
        except Exception as e:
            if "model_id" in str(e) and "string_type" in str(e):
                error_msg = "No Model ID entered, please enter it in the following format: `%%ai <model_id>`"
                print(error_msg, file=sys.stderr)
                return
            if not args:
                print(
                    "No valid %ai magics arguments given, run `%ai help` for all options.",
                    file=sys.stderr,
                )
                return
            raise e

        if args == 0 and self.initial_language_model is None:
            # this happens when `--help` is called on the root command, in which
            # case we want to exit early.
            return

        # If a value error occurs, don't print the full stacktrace
        try:
            if args.type == "fix":
                return self.handle_fix(args)
            if args.type == "help":
                return self.handle_help(args)
            if args.type == "list":
                return self.handle_list(args)
            if args.type == "alias":
                return self.handle_alias(args)
            if args.type == "dealias":
                return self.handle_dealias(args)
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

        # エラーハンドルモードではセルを通常実行し、失敗時のみLLMへ情報を渡す
        if args.error_handle:
            return self.run_cell_with_error_handle(args, cell)

        prompt = cell.strip()

        return self.run_ai_cell(args, prompt)

    def run_ai_cell(self, args: CellArgs, prompt: str):
        """
        Handles the `%%ai` cell magic. This is the main method that invokes the
        language model.
        """
        # Interpolate local variables into prompt.
        # For example, if a user runs `a = "hello"` and then runs `%%ai {a}`, it
        # should be equivalent to running `%%ai hello`.
        ip = self.shell
        prompt = prompt.format_map(FormatDict(ip.user_ns))

        # Prepare messages for the model
        messages = []
        # Test 20251116 self.transcriptの取り込みをしないようにする
        # Add conversation history if available
        # if self.transcript:
        #     messages.extend(self.transcript[-2 * self.max_history :])

        # Test 20251116 Start
        # 以下実装により、%%ai --nb-path ~~~で受け取った値を、args.nb_pathから受け取ることができる。
        # parserの@click.optionに--nb-pathというオプションを追加
        # parserのCellArgsにnb_pathを追加

        # %configからデフォルト値を設定できるようにする。
        # if hasattr(args, "nb_path") and args.nb_path is None and self.default_nb_path:
        #     args.nb_path = self.default_nb_path

        # if getattr(args, "nb_path", None):
        #     # 試しに受け取った内容を表示する
        #     # print(f"--nb-path={args.nb_path}", file=sys.stderr)
        #     # print(f"default_nb_path={self.default_nb_path}", file=sys.stderr)
        #     # nb = self.list_cells(args.nb_path)
        #     # print(f"cell0= {nb[0]}", file=sys.stderr)
        #     # print(f"cell1= {nb[1]}", file=sys.stderr)
        #     # print(f"cell2= {nb[2]}", file=sys.stderr)

        #     # self.transcriptの代わりに、取得したノートブックの内容をテキストとしてcontentにぶち込んでみる
        #     # →入力が長すぎると怒られたため、ちゃんとパースしてあげる必要があるかもしれない。
        #     # nb_text = self.load_nb_as_text(args.nb_path)
        #     # messages.append({"role": "user", "content": nb_text})
        #     # print(f"nb text head 100: {nb_text[0:100]}")

        #     # ノートブックを適当にパースしてmessagesに追加
        #     print(f"参照ノートブックPath: {args.nb_path}")
        #     # print(f"ipn test: {ipn.path()}")
        #     nb = self.load_nb(args.nb_path)
        #     messages.extend(self.cells_to_messages(args.nb_path))
        #     messages.append({"role": "user", "content": "上記は、読み込んだノートブックのセルを羅列したリストです。セルの配置順をcell_indexに、コードセルの実行順をexecution_countに格納しています。この情報を前提に以降の質問に回答してください。"})

            # return
        # Test 20251116 End

        # フロント拡張からノートブックの内容を受け取ってLLMに渡す。
        prefix_raw = ip.user_ns.get("__AI_NOTEBOOK_PREFIX__")
        # print(f"prefix_raw: {prefix_raw}")
        if prefix_raw is not None:
            nb = nbf.reads(prefix_raw, as_version=4)
            messages.extend(self.cells_to_messages(nb))
            messages.append({"role": "user", "content": "上記は、読み込んだノートブックのセルを羅列したリストです。セルの配置順をcell_indexに、コードセルの実行順をexecution_countに格納しています。この情報を前提に以降の質問に回答してください。"})

        # 外部ファイル読み込みしてみる。
        if getattr(args, "option_file", None):
            print(f"--option-file={args.option_file}")
            file_path = args.option_file
            f = open(file_path, 'r')
            file_str = f.read()
            f.close()
            messages.append({"role": "user", "content": "以下に、回答の前提として欲しいファイルのパスと内容を示します。"})
            messages.append({"role": "user", "content": f"option file path: {file_path}"})
            messages.append({"role": "user", "content": file_str})

        # Add current prompt
        messages.append({"role": "user", "content": prompt})

        # Resolve model_id: check if it's in CHAT_MODELS or an alias
        model_id = args.model_id
        # Check if model_id is an alias and get stored configuration
        alias_config = None
        if model_id not in CHAT_MODELS and model_id in self.aliases:
            alias_config = self.aliases[model_id]
            model_id = alias_config["target"]
            # Use stored api_base and api_key_name if not provided in current call
            if not args.api_base and alias_config["api_base"]:
                args.api_base = alias_config["api_base"]
            if not args.api_key_name and alias_config["api_key_name"]:
                args.api_key_name = alias_config["api_key_name"]
        elif model_id not in CHAT_MODELS:
            error_msg = f"Model ID '{model_id}' is not a known model or alias. Run '%ai list' to see available models and aliases."
            print(error_msg, file=sys.stderr)  # Log to stderr
            return
        try:
            # Prepare litellm completion arguments
            completion_args = {"model": model_id, "messages": messages, "stream": False}

            # Add api_base if provided
            if args.api_base:
                completion_args["api_base"] = args.api_base

            # Add API key from .env if api_key_name is provided
            if args.api_key_name:
                # Retrieve the actual API key from the .env file
                api_key_name_value = os.getenv(args.api_key_name)
                if not api_key_name_value:
                    error_msg = f"API key '{args.api_key_name}' not found in .env file."
                    print(error_msg, file=sys.stderr)
                    return
                completion_args["api_key_name"] = api_key_name_value

            # Call litellm completion
            response = litellm.completion(**completion_args)

            # Extract output text from response
            output = response.choices[0].message.content

            # Append exchange to transcript
            self._append_exchange(prompt, output)

            # Set model ID in metadata
            metadata = {"jupyter_ai_v3": {"model_id": args.model_id}}

            # Return output given the format
            return self.display_output(output, args.format, metadata)

        except Exception as e:
            error_msg = f"Error calling language model: {str(e)}"
            print(error_msg, file=sys.stderr)
            return error_msg
    # Test 20251116 Start

    # ファイルをjson形式のテキストとして取得する
    def load_nb_as_text(self, nb_path: str):
        f = open(nb_path, 'r')
        nb_text = f.read()
        f.close()
        return nb_text

    # ファイルをノートブックとして解釈して読み込む
    def load_nb(self, nb_path: str):
        return nbf.read(nb_path, as_version=4)

    # 読み込んだノートブックをセルのリストの形に整形する
    def list_cells(self, nb_path: str):
        nb = self.load_nb(nb_path)
        cells = []
        for i, c in enumerate(nb.cells):
            cells.append({
                "index": i,
                "type": c["cell_type"],          # "code" or "markdown"
                "source": c.get("source", ""),   # セル本文
                "output": c.get("outputs", "")   # 出力結果
            })
        return cells

    # 読み込んだノートブックをmessage形式に整形する。
    def cells_to_messages(self, nb):
        messages = []
        for i, c in enumerate(nb.cells):
            source = "".join(c.get("source", ""))
            if c["cell_type"] == "markdown":
                content = {
                    "cell_index": i,
                    "cell_type": c["cell_type"],
                    "source": source
                }
            elif c["cell_type"] == "code":
                content = {
                    "cell_index": i,
                    "execution_count": c.get("execution_count", ""),
                    "cell_type": c["cell_type"],
                    "source": source,
                    "outputs": c.get("outputs", "")
                }
            else:
                continue

            content = json.dumps(content)
            messages.append({
                "role": "user",
                "content": content,
            })
        return messages

    # いらないかも
    def code_cells(self, nb_path: str):
        nb = self.load_nb(nb_path)
        return [c["source"] for c in nb.cells if c["cell_type"] == "code"]

    def markdown_cells(self, nb_path: str):
        nb = self.load_nb(nb_path)
        return [c["source"] for c in nb.cells if c["cell_type"] == "markdown"]
    # Test 20251116 End

    def run_cell_with_error_handle(self, args: CellArgs, cell: str):
        # セルを通常通り実行し、例外発生時のみLLMに説明を依頼する
        ip = self.shell
        try:
            exec_result = ip.run_cell(cell)
        except BaseException as exc:
            traceback_text = "".join(
                traceback.TracebackException.from_exception(exc).format()
            )
            return self._handle_cell_error(args, cell, traceback_text)

        if not exec_result or getattr(exec_result, "success", True):
            return

        error_exc = getattr(exec_result, "error_in_exec", None) or getattr(
            exec_result, "error_before_exec", None
        )
        if not error_exc:
            return

        traceback_text = "".join(
            traceback.TracebackException.from_exception(error_exc).format()
        )
        return self._handle_cell_error(args, cell, traceback_text)

    def _handle_cell_error(self, args: CellArgs, cell: str, traceback_text: str):
        # 実行したコードとトレースバックをテンプレートへ埋め込んでLLMへ送る
        if not traceback_text:
            return

        template = self._get_error_help_prompt()
        prompt = template.format(code=cell.strip(), error=traceback_text.strip())
        safe_prompt = prompt.replace("{", "{{").replace("}", "}}")

        values = args.model_dump()
        values["error_handle"] = False
        helper_args = CellArgs(**values)

        print(
            "An error was detected while executing the cell. Asking the AI assistant for help."
        )
        return self.run_ai_cell(helper_args, safe_prompt)

    def _get_error_help_prompt(self) -> str:
        """
        Returns the prompt template for error handling, preferring an external file if present.
        """
        candidate_path = self.error_help_prompt_path or os.path.join(
            os.getcwd(), "errorhandle_prompt.cfg"
        )

        if candidate_path and os.path.isfile(candidate_path):
            try:
                with open(candidate_path, "r", encoding="utf-8") as f:
                    return f.read()
            except OSError as exc:
                print(
                    f"Failed to read error prompt file at {candidate_path}: {exc}",
                    file=sys.stderr,
                )

        # フォールバックは組み込みのデフォルト（日本語）
        return self.error_help_prompt

    def display_output(self, output, display_format, metadata: dict[str, Any]) -> Any:
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
        """
        self.transcript.append({"role": "user", "content": prompt})
        self.transcript.append({"role": "assistant", "content": output})
        # Keep only the most recent `self.max_history * 2` messages
        max_len = self.max_history * 2
        if len(self.transcript) > max_len:
            self.transcript = self.transcript[-max_len:]

    def handle_help(self, _: HelpArgs) -> None:
        """
        Handles `%ai help`. Prints a help message via `click.echo()`.
        """
        # The line parser's help function prints both cell and line help
        with click.Context(line_magic_parser, info_name=r"%ai") as ctx:
            click.echo(line_magic_parser.get_help(ctx))

    def handle_dealias(self, args: DeleteArgs) -> TextOrMarkdown:
        """
        Handles `%ai dealias`. Deletes a model alias.
        """

        if args.name in AI_COMMANDS:
            raise ValueError(
                f"Reserved command names, including {args.name}, cannot be deleted"
            )

        if args.name not in self.aliases:
            raise ValueError(f"There is no alias called {args.name}")

        del self.aliases[args.name]
        output = f"Deleted alias `{args.name}`"
        return TextOrMarkdown(output, output)

    def handle_reset(self, args: ResetArgs) -> None:
        """
        Handles `%ai reset`. Clears the history.
        """
        self.transcript = []

    def handle_fix(self, args: FixArgs) -> Any:
        """
        Handles `%ai fix`. Meant to provide fixes for any exceptions raised in
        the kernel while running cells.

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

        prompt = f"Explain the following error and propose a fix:\n\n{last_error}"
        # Set CellArgs based on FixArgs
        values = args.model_dump()
        values["type"] = "root"
        cell_args = CellArgs(**values)
        print("I will attempt to explain and fix the error. ")

        return self.run_ai_cell(cell_args, prompt)

    def handle_alias(self, args: RegisterArgs) -> TextOrMarkdown:
        """
        Handles `%ai alias`. Adds an alias for a model ID for future calls.
        """
        # Existing command names are not allowed
        if args.name in AI_COMMANDS:
            raise ValueError(f"The name {args.name} is reserved for a command")

        # Store the alias with its configuration
        self.aliases[args.name] = {
            "target": args.target,
            "api_base": args.api_base,
            "api_key_name": args.api_key_name,
        }

        output = f"Registered new alias `{args.name}`"
        return TextOrMarkdown(output, output)

    def handle_version(self, args: VersionArgs) -> str:
        """
        Handles `%ai version`. Returns the current version of
        `jupyter_ai_magics`.
        """
        return __version__



    def handle_list(self, args: ListArgs):
        """
        Handles `%ai list`.
         - `%ai list` shows all providers by default, and ask the user to run %ai list <provider-name>.
         - `%ai list <provider-name>` shows all models available from one provider. It should also note that the list is not comprehensive, and include a reference to the upstream LiteLLM docs.
         - `%ai list all` should list all models.
        """
        # Get list of available models from litellm
        models = CHAT_MODELS

        # If provider_id is None, only return provider IDs
        if getattr(args, "provider_id", None) is None:
            # Extract unique provider IDs from model IDs
            provider_ids = set()
            for model in models:
                if "/" in model:
                    provider_ids.add(model.split("/")[0])

            # Format output for both text and markdown
            text_output = "Available providers\n\n (Run `%ai list <provider_name>` to see models for a specific provider)\n\n"
            markdown_output = "## Available providers\n\n (Run `%ai list <provider_name>` to see models for a specific provider)\n\n"

            for provider_id in sorted(provider_ids):
                text_output += f"* {provider_id}\n"
                markdown_output += f"* `{provider_id}`\n"

            return TextOrMarkdown(text_output, markdown_output)

        elif getattr(args, "provider_id", None) == "all":
            # Otherwise show all models and aliases
            text_output = "All available models\n\n  (The list is not comprehensive, a list of models is available at https://docs.litellm.ai/docs/providers)\n\n"
            markdown_output = "## All available models \n\n (The list is not comprehensive, a list of models is available at https://docs.litellm.ai/docs/providers)\n\n"

            for model in models:
                text_output += f"* {model}\n"
                markdown_output += f"* `{model}`\n"

            # Also list any custom aliases
            if len(self.aliases) > 0:
                text_output += "\nAliases:\n"
                markdown_output += "\n### Aliases\n\n"
                for alias, config in self.aliases.items():
                    text_output += f"* {alias}:\n"
                    text_output += f"  - target: {config['target']}\n"
                    if config["api_base"]:
                        text_output += f"  - api_base: {config['api_base']}\n"
                    if config["api_key_name"]:
                        text_output += f"  - api_key_name: {config['api_key_name']}\n"

                    markdown_output += f"* `{alias}`:\n"
                    markdown_output += f"  - target: `{config['target']}`\n"
                    if config["api_base"]:
                        markdown_output += f"  - api_base: `{config['api_base']}`\n"
                    if config["api_key_name"]:
                        markdown_output += (
                            f"  - api_key_name: `{config['api_key_name']}`\n"
                        )

            return TextOrMarkdown(text_output, markdown_output)

        else:
            # If a specific provider_id is given, filter models by that provider
            provider_id = args.provider_id
            filtered_models = [m for m in models if m.startswith(provider_id + "/")]

            if not filtered_models:
                return TextOrMarkdown(
                    f"No models found for provider '{provider_id}'.",
                    f"No models found for provider `{provider_id}`.",
                )

            text_output = f"Available models for provider '{provider_id}'\n\n (The list is not comprehensive, a list of models is available at https://docs.litellm.ai/docs/providers/{provider_id})\n\n"
            markdown_output = f"## Available models for provider `{provider_id}`\n\n (The list is not comprehensive, a list of models is available at https://docs.litellm.ai/docs/providers/{provider_id})\n\n"

            for model in filtered_models:
                text_output += f"* {model}\n"
                markdown_output += f"* `{model}`\n"

            # Also list any custom aliases for this provider
            if len(self.aliases) > 0:
                text_output += "\nAliases:\n"
                markdown_output += "\n### Aliases\n\n"
                for alias, config in self.aliases.items():
                    if config["target"].startswith(provider_id + "/"):
                        text_output += f"* {alias}:\n"
                        text_output += f"  - target: {config['target']}\n"
                        if config["api_base"]:
                            text_output += f"  - api_base: {config['api_base']}\n"
                        if config["api_key_name"]:
                            text_output += (
                                f"  - api_key_name: {config['api_key_name']}\n"
                            )

                        markdown_output += f"* `{alias}`:\n"
                        markdown_output += f"  - target: `{config['target']}`\n"
                        if config["api_base"]:
                            markdown_output += f"  - api_base: `{config['api_base']}`\n"
                        if config["api_key_name"]:
                            markdown_output += (
                                f"  - api_key_name: `{config['api_key_name']}`\n"
                            )

            return TextOrMarkdown(text_output, markdown_output)
    # エラー説明用テンプレート（コード／トレースバックを差し込む）
    error_help_prompt = traitlets.Unicode(
        default_value=(
            "あなたは Jupyter セルのエラーを解説し、修正方針を提案する AI アシスタントです。\n\n"
            "次の情報を基に、原因の仮説と具体的な修正ステップを日本語で短く記述してください。\n"
            "- セルソース:\n{code}\n\n"
            "- エラートレースバック:\n{error}\n"
        ),
        help="""Template used when `--error-handle` is supplied.

        The template should reference `{code}` and `{error}` placeholders, which will be replaced
        with the executed cell contents and the formatted traceback respectively.""",
        config=True,
    )

    # 外部ファイルからプロンプトを読む場合のパス（未設定ならリポジトリ直下 errorhandle_prompt.cfg を試す）
    error_help_prompt_path = traitlets.Unicode(
        default_value=None,
        allow_none=True,
        help="""Optional path to a file containing the error-help prompt template.
        If set (or if a default file exists at workspace root), its contents will be used instead of `error_help_prompt`.
        The template must include `{code}` and `{error}` placeholders.""",
        config=True,
    )
