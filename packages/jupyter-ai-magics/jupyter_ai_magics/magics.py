import json
import os
import warnings
from typing import Optional

from importlib_metadata import entry_points
from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, line_cell_magic
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring
from IPython.display import HTML, Markdown, Math, JSON

from .providers import BaseProvider


MODEL_ID_ALIASES = {
    "gpt2": "huggingface_hub:gpt2",
    "gpt3": "openai:text-davinci-003",
    "chatgpt": "openai-chat:gpt-3.5-turbo",
    "gpt4": "openai-chat:gpt-4",
}

class TextWithMetadata(object):

    def __init__(self, text, metadata):
        self.text = text
        self.metadata = metadata

    def _repr_mimebundle_(self, include=None, exclude=None):
        return ({'text/plain': self.text}, self.metadata)

DISPLAYS_BY_FORMAT = {
    "code": None,
    "html": HTML,
    "markdown": Markdown,
    "math": Math,
    "md": Markdown,
    "json": JSON,
    "text": TextWithMetadata
}

MARKDOWN_PROMPT_TEMPLATE = '{prompt}\n\nProduce output in markdown format only.'

PROMPT_TEMPLATES_BY_FORMAT = {
    "code": '{prompt}\n\nProduce output as source code only, with no text or explanation before or after it.',
    "html": '{prompt}\n\nProduce output in HTML format only, with no markup before or afterward.',
    "markdown": MARKDOWN_PROMPT_TEMPLATE,
    "md": MARKDOWN_PROMPT_TEMPLATE,
    "math": '{prompt}\n\nProduce output in LaTeX format only, with $$ at the beginning and end.',
    "json": '{prompt}\n\nProduce output in JSON format only, with nothing before or after it.',
    "text": '{prompt}' # No customization
}

AI_COMMANDS = {
    "help": "Display a list of supported commands",
    "list": "Display a list of models that you can use"
}

class FormatDict(dict):
    """Subclass of dict to be passed to str#format(). Suppresses KeyError and
    leaves replacement field unchanged if replacement field is not associated
    with a value."""
    def __missing__(self, key): 
        return key.join("{}")

class EnvironmentError(BaseException):
    pass

@magics_class
class AiMagics(Magics):
    def __init__(self, shell):
        super(AiMagics, self).__init__(shell)
        self.transcript_openai = []

        # suppress warning when using old OpenAIChat provider
        warnings.filterwarnings("ignore", message="You are trying to use a chat model. This way of initializing it is "
            "no longer supported. Instead, please use: "
            "`from langchain.chat_models import ChatOpenAI`")

        # load model providers from entry point
        self.providers = {}
        eps = entry_points()
        model_provider_eps = eps.select(group="jupyter_ai.model_providers")
        for model_provider_ep in model_provider_eps:
            try:
                Provider = model_provider_ep.load()
            except:
                continue
            self.providers[Provider.id] = Provider
    
    # Run an AI command using the arguments provided as a space-delimited value
    def _ai_command(self, command, args_string):
        args = args_string.split() # Split by whitespace

        # When we can use Python 3.10+, replace this with a 'match' command
        if (command == 'help'):
            return "Running help"
        elif (command == 'list'):
            return "Running list"
        else:
            return f"Command not recognized: {command}"

    def _append_exchange_openai(self, prompt: str, output: str):
        """Appends a conversational exchange between user and an OpenAI Chat
        model to a transcript that will be included in future exchanges."""
        self.transcript_openai.append({
            "role": "user",
            "content": prompt
        })
        self.transcript_openai.append({
            "role": "assistant",
            "content": output
        })

    def _decompose_model_id(self, model_id: str):
        """Breaks down a model ID into a two-tuple (provider_id, local_model_id). Returns (None, None) if indeterminate."""
        if model_id in MODEL_ID_ALIASES:
            model_id = MODEL_ID_ALIASES[model_id]

        if ":" not in model_id:
            # case: model ID was not provided with a prefix indicating the provider
            # ID. try to infer the provider ID before returning (None, None).

            # naively search through the dictionary and return the first provider
            # that provides a model of the same ID.
            for provider_id, Provider in self.providers.items():
                if model_id in Provider.models:
                    return (provider_id, model_id)
            
            return (None, None)

        provider_id, local_model_id = model_id.split(":", 1)
        return (provider_id, local_model_id)

    def _get_provider(self, provider_id: Optional[str]) -> BaseProvider:
        """Returns the model provider ID and class for a model ID. Returns None if indeterminate."""
        if provider_id is None or provider_id not in self.providers:
            return None

        return self.providers[provider_id]

    @magic_arguments()
    @argument('model_id',
                help="""Model to run, specified as a model ID that may be
                optionally prefixed with the ID of the model provider, delimited
                by a colon.""")
    @argument('-f', '--format',
                choices=["code", "markdown", "html", "json", "math", "md", "text"],
                nargs="?",
                default="markdown",
                help="""IPython display to use when rendering output. [default="markdown"]""")
    @argument('-r', '--reset',
                action="store_true",
                help="""Clears the conversation transcript used when interacting
                with an OpenAI chat model provider. Does nothing with other
                providers.""")
    @argument('prompt',
                nargs='*',
                help="""Prompt for code generation. When used as a line magic, it
                runs to the end of the line. In cell mode, the entire cell is
                considered the code generation prompt.""")
    @line_cell_magic
    def ai(self, line, cell=None):
        # parse arguments
        args = parse_argstring(self.ai, line)
        if cell is None:
            prompt = ' '.join(args.prompt)
        else:
            prompt = cell
        
        # If the user is attempting to run a command, run the command separately.
        if (args.model_id in AI_COMMANDS):
            # The "prompt" is a list of arguments to the command, whitespace-delimited
            return self._ai_command(args.model_id, prompt)

        # Apply a prompt template.
        prompt = PROMPT_TEMPLATES_BY_FORMAT[args.format].format(prompt = prompt)

        # determine provider and local model IDs
        provider_id, local_model_id = self._decompose_model_id(args.model_id)
        Provider = self._get_provider(provider_id)
        if Provider is None:
            return f"Cannot determine model provider from model ID {args.model_id}."

        # if `--reset` is specified, reset transcript and return early
        if (provider_id == "openai-chat" and args.reset):
            self.transcript_openai = []
            return

        # validate presence of authn credentials
        auth_strategy = self.providers[provider_id].auth_strategy
        if auth_strategy:
            # TODO: handle auth strategies besides EnvAuthStrategy
            if auth_strategy.type == "env" and auth_strategy.name not in os.environ:
                raise EnvironmentError(
                    f"Authentication environment variable {auth_strategy.name} not provided.\n"
                    f"An authentication token is required to use models from the {Provider.name} provider.\n"
                    f"Please specify it via `%env {auth_strategy.name}=token`. "
                ) from None
        
        # interpolate user namespace into prompt
        ip = get_ipython()
        prompt = prompt.format_map(FormatDict(ip.user_ns))

        # configure and instantiate provider
        provider_params = { "model_id": local_model_id }
        if provider_id == "openai-chat":
            provider_params["prefix_messages"] = self.transcript_openai
        provider = Provider(**provider_params)

        # generate output from model via provider
        result = provider.generate([prompt])
        output = result.generations[0][0].text

        # if openai-chat, append exchange to transcript
        if provider_id == "openai-chat":
            self._append_exchange_openai(prompt, output)

        # build output display
        DisplayClass = DISPLAYS_BY_FORMAT[args.format]

        md = {
            "jupyter_ai": {
                "provider_id": provider_id,
                "model_id": local_model_id
            }
        }

        # if the user wants code, add another cell with the output.
        if args.format == 'code':
            # Strip leading and trailing triple-backticks
            output = output.removeprefix('```\n').removesuffix('\n```')
            new_cell_payload = dict(
                source='set_next_input',
                text=output,
                replace=False,
            )
            ip.payload_manager.write_payload(new_cell_payload)
            return HTML('AI generated code inserted below &#11015;&#65039;', metadata=md); # No output from the AI cell

        if DisplayClass is None:
            return output
        if args.format == 'json':
            # JSON display expects a dict, not a JSON string
            output = json.loads(output)
        output_display = DisplayClass(output, metadata=md)

        # finally, display output display
        return output_display
