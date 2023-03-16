import os
import json
from typing import Dict, Optional, Any

from IPython import get_ipython
from IPython.core.magic import Magics, magics_class, line_cell_magic
from IPython.core.magic_arguments import magic_arguments, argument, parse_argstring
from IPython.display import display, HTML, Markdown, Math, JSON

from pydantic import ValidationError
from langchain.llms import type_to_cls_dict
from langchain.llms.openai import OpenAIChat

LANGCHAIN_LLM_DICT = type_to_cls_dict.copy()
LANGCHAIN_LLM_DICT["openai-chat"] = OpenAIChat

PROVIDER_SCHEMAS: Dict[str, Any] = {
    # AI21 model provider currently only provides its prompt via the `prompt`
    # key, which limits the models that can actually be used.
    # Reference: https://docs.ai21.com/reference/j2-complete-api
    "ai21": {
        "models": ["j1-large", "j1-grande", "j1-jumbo", "j1-grande-instruct", "j2-large", "j2-grande", "j2-jumbo", "j2-grande-instruct", "j2-jumbo-instruct"],
        "model_id_key": "model",
        "auth_envvar": "AI21_API_KEY"
    },
    # Anthropic model provider supports any model available via
    # `anthropic.Client#completion()`.
    # Reference: https://console.anthropic.com/docs/api/reference
    "anthropic": {
        "models": ["claude-v1", "claude-v1.0", "claude-v1.2", "claude-instant-v1", "claude-instant-v1.0"],
        "model_id_key": "model",
        "auth_envvar": "ANTHROPIC_API_KEY"
    },
    # Cohere model provider supports any model available via
    # `cohere.Client#generate()`.`
    # Reference: https://docs.cohere.ai/reference/generate
    "cohere": {
        "models": ["medium", "xlarge"],
        "model_id_key": "model",
        "auth_envvar": "COHERE_API_KEY"
    },
    "huggingface_hub": {
        "models": ["*"],
        "model_id_key": "repo_id",
        "auth_envvar": "HUGGINGFACEHUB_API_TOKEN"
    },
    "huggingface_endpoint": {
        "models": ["*"],
        "model_id_key": "endpoint_url",
        "auth_envvar": "HUGGINGFACEHUB_API_TOKEN"
    },
    # OpenAI model provider supports any model available via
    # `openai.Completion`.
    # Reference: https://platform.openai.com/docs/models/model-endpoint-compatibility
    "openai": {
        "models": ['text-davinci-003', 'text-davinci-002', 'text-curie-001', 'text-babbage-001', 'text-ada-001', 'davinci', 'curie', 'babbage', 'ada'],
        "model_id_key": "model_name",
        "auth_envvar": "OPENAI_API_KEY"
    },
    # OpenAI chat model provider supports any model available via
    # `openai.ChatCompletion`.
    # Reference: https://platform.openai.com/docs/models/model-endpoint-compatibility
    "openai-chat": {
        "models": ['gpt-4', 'gpt-4-0314', 'gpt-4-32k', 'gpt-4-32k-0314', 'gpt-3.5-turbo', 'gpt-3.5-turbo-0301'],
        "model_id_key": "model_name",
        "auth_envvar": "OPENAI_API_KEY"
    },
    "sagemaker_endpoint": {
        "models": ["*"],
        "model_id_key": "endpoint_name",
    },
}

MODEL_ID_ALIASES = {
    "gpt2": "huggingface_hub:gpt2",
    "gpt3": "openai:text-davinci-003",
    "chatgpt": "openai-chat:gpt-3.5-turbo",
    "gpt4": "openai-chat:gpt-4",
}

DISPLAYS_BY_FORMAT = {
    "html": HTML,
    "markdown": Markdown,
    "math": Math,
    "md": Markdown,
    "json": JSON,
}

def decompose_model_id(model_id: str):
    """Breaks down a model ID into a two-tuple (provider_id, local_model_id). Returns (None, None) if indeterminate."""
    if model_id in MODEL_ID_ALIASES:
        model_id = MODEL_ID_ALIASES[model_id]

    if ":" not in model_id:
        # case: model ID was not provided with a prefix indicating the provider
        # ID. try to infer the provider ID before returning (None, None).

        # naively search through the dictionary and return the first provider
        # that provides a model of the same ID.
        for provider_id, provider_schema in PROVIDER_SCHEMAS.items():
            if model_id in provider_schema["models"]:
                return (provider_id, model_id)
        
        return (None, None)

    possible_provider_id, local_model_id = model_id.split(":", 1)

    if possible_provider_id not in ("http", "https"):
        # case (happy path): provider ID was specified
        return (possible_provider_id, local_model_id)
    
    # else case: model ID is a URL to some endpoint. right now, the only
    # provider that accepts a raw URL is huggingface_endpoint.
    return ("huggingface_endpoint", local_model_id)

def get_provider(provider_id: Optional[str]):
    """Returns the model provider ID and class for a model ID. Returns None if indeterminate."""
    if provider_id is None or provider_id not in LANGCHAIN_LLM_DICT:
        return None

    return LANGCHAIN_LLM_DICT[provider_id]

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
    
    def append_exchange_openai(self, prompt: str, output: str):
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

    @magic_arguments()
    @argument('model_id',
                help="""Model to run, specified as a model ID that may be
                optionally prefixed with the ID of the model provider, delimited
                by a colon.""")
    @argument('-f', '--format',
                choices=["markdown", "html", "json", "math", "md"],
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
        
        # determine provider and local model IDs
        provider_id, local_model_id = decompose_model_id(args.model_id)
        if provider_id is None:
            return display("Cannot determine model provider.")

        # if `--reset` is specified, reset transcript and return early
        if (provider_id == "openai-chat" and args.reset):
            self.transcript_openai = []
            return

        # validate presence of authn credentials
        auth_envvar = PROVIDER_SCHEMAS[provider_id].get("auth_envvar")
        if auth_envvar and auth_envvar not in os.environ:
            raise EnvironmentError(
                f"Authentication environment variable {auth_envvar} not provided.\n"
                f"An authentication token is required to use models from the {provider_id} provider.\n"
                f"Please specify it via `%env {auth_envvar}=token`. "
            ) from None
        
        # interpolate user namespace into prompt
        ip = get_ipython()
        prompt = prompt.format_map(FormatDict(ip.user_ns))

        # configure and instantiate provider
        ProviderClass = get_provider(provider_id)
        model_id_key = PROVIDER_SCHEMAS[provider_id]['model_id_key']
        provider_params = {}
        provider_params[model_id_key] = local_model_id
        if provider_id == "openai-chat":
            provider_params["prefix_messages"] = self.transcript_openai
        provider = ProviderClass(**provider_params)

        # generate output from model via provider
        result = provider.generate([prompt])
        output = result.generations[0][0].text

        # if openai-chat, append exchange to transcript
        if provider_id == "openai-chat":
            self.append_exchange_openai(prompt, output)

        # build output display
        DisplayClass = DISPLAYS_BY_FORMAT[args.format]
        if args.format == 'json':
            # JSON display expects a dict, not a JSON string
            output = json.loads(output)
        output_display = DisplayClass(output)

        # finally, display output display
        return display(output_display)
