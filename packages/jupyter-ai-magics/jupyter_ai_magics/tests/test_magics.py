import os
from unittest.mock import Mock, patch

import pytest
from IPython import InteractiveShell
from IPython.core.display import Markdown
from jupyter_ai_magics.magics import AiMagics
from langchain_core.messages import AIMessage, HumanMessage
from pytest import fixture
from traitlets.config.loader import Config
import re
import json
from unittest.mock import Mock
from IPython.display import HTML, Markdown, JSON
from jupyter_ai_magics.magics import AiMagics, DISPLAYS_BY_FORMAT


@fixture
def ip() -> InteractiveShell:
    ip = InteractiveShell()
    ip.config = Config()
    return ip


def test_aliases_config(ip):
    ip.config.AiMagics.aliases = {"my_custom_alias": "my_provider:my_model"}
    ip.extension_manager.load_extension("jupyter_ai_magics")
    providers_list = ip.run_line_magic("ai", "list").text
    assert "my_custom_alias" in providers_list


def test_default_model_cell(ip):
    ip.config.AiMagics.default_language_model = "my-favourite-llm"
    ip.extension_manager.load_extension("jupyter_ai_magics")
    with patch.object(AiMagics, "run_ai_cell", return_value=None) as mock_run:
        ip.run_cell_magic("ai", "", cell="Write code for me please")
        assert mock_run.called
        cell_args = mock_run.call_args.args[0]
        assert cell_args.model_id == "my-favourite-llm"


def test_non_default_model_cell(ip):
    ip.config.AiMagics.default_language_model = "my-favourite-llm"
    ip.extension_manager.load_extension("jupyter_ai_magics")
    with patch.object(AiMagics, "run_ai_cell", return_value=None) as mock_run:
        ip.run_cell_magic("ai", "some-different-llm", cell="Write code for me please")
        assert mock_run.called
        cell_args = mock_run.call_args.args[0]
        assert cell_args.model_id == "some-different-llm"


def test_default_model_error_line(ip):
    ip.config.AiMagics.default_language_model = "my-favourite-llm"
    ip.extension_manager.load_extension("jupyter_ai_magics")
    with patch.object(AiMagics, "handle_error", return_value=None) as mock_run:
        ip.run_cell_magic("ai", "error", cell=None)
        assert mock_run.called
        cell_args = mock_run.call_args.args[0]
        assert cell_args.model_id == "my-favourite-llm"


PROMPT = HumanMessage(
    content=("Write code for me please\n\nProduce output in markdown format only.")
)
RESPONSE = AIMessage(content="Leet code")
AI1 = AIMessage("ai1")
H1 = HumanMessage("h1")
AI2 = AIMessage("ai2")
H2 = HumanMessage("h2")
AI3 = AIMessage("ai3")


@pytest.mark.parametrize(
    ["transcript", "max_history", "expected_context"],
    [
        ([], 3, [PROMPT]),
        ([AI1], 0, [PROMPT]),
        ([AI1], 1, [AI1, PROMPT]),
        ([H1, AI1], 0, [PROMPT]),
        ([H1, AI1], 1, [H1, AI1, PROMPT]),
        ([AI1, H1, AI2], 0, [PROMPT]),
        ([AI1, H1, AI2], 1, [H1, AI2, PROMPT]),
        ([AI1, H1, AI2], 2, [AI1, H1, AI2, PROMPT]),
        ([H1, AI1, H2, AI2], 0, [PROMPT]),
        ([H1, AI1, H2, AI2], 1, [H2, AI2, PROMPT]),
        ([H1, AI1, H2, AI2], 2, [H1, AI1, H2, AI2, PROMPT]),
        ([AI1, H1, AI2, H2, AI3], 0, [PROMPT]),
        ([AI1, H1, AI2, H2, AI3], 1, [H2, AI3, PROMPT]),
        ([AI1, H1, AI2, H2, AI3], 2, [H1, AI2, H2, AI3, PROMPT]),
        ([AI1, H1, AI2, H2, AI3], 3, [AI1, H1, AI2, H2, AI3, PROMPT]),
    ],
)
def test_max_history(ip, transcript, max_history, expected_context):
    ip.extension_manager.load_extension("jupyter_ai_magics")
    ai_magics = ip.magics_manager.registry["AiMagics"]
    ai_magics.transcript = transcript.copy()
    ai_magics.max_history = max_history
    provider = ai_magics._get_provider("openrouter")
    with (
        patch.object(provider, "generate") as generate,
        patch.dict(os.environ, OPENROUTER_API_KEY="123"),
    ):
        generate.return_value.generations = [[Mock(text="Leet code")]]
        result = ip.run_cell_magic(
            "ai",
            "openrouter:anthropic/claude-3.5-sonnet",
            cell="Write code for me please",
        )
        provider.generate.assert_called_once_with([expected_context])
    assert isinstance(result, Markdown)
    assert result.data == "Leet code"
    assert result.filename is None
    assert result.metadata == {
        "jupyter_ai": {
            "model_id": "anthropic/claude-3.5-sonnet",
            "provider_id": "openrouter",
        }
    }
    assert result.url is None
    assert ai_magics.transcript == [*transcript, PROMPT, RESPONSE]


def test_reset(ip):
    ip.extension_manager.load_extension("jupyter_ai_magics")
    ai_magics = ip.magics_manager.registry["AiMagics"]
    ai_magics.transcript = [AI1, H1, AI2, H2, AI3]
    result = ip.run_line_magic("ai", "reset")
    assert ai_magics.transcript == []
    class DummyShell:
       def __init__(self):
            self.set_next_input = Mock()
            self.user_ns = {}
            self.execution_count = 1

    @pytest.fixture
    def dummy_shell():
        return DummyShell()

    @pytest.fixture
    def ai_magics(dummy_shell):
        return AiMagics(shell=dummy_shell)

    def test_display_output_code_format(ai_magics, dummy_shell):
        original_output = "   ```python\n" + "def add(a, b):\n    return a+b" + "\n```"
        md = {"test_meta": "value"}
        result = ai_magics.display_output(original_output, "code", md)
  
        expected_output = "def add(a, b):\n    return a+b"
        dummy_shell.set_next_input.assert_called_once_with(expected_output, replace=False)
    
        assert isinstance(result, HTML)
        assert result.metadata == md
        assert "AI generated code inserted below" in result.data

    def test_display_output_markdown_format(ai_magics):
        output_text = "This is **markdown** output."
        md = {"jupyter_ai": {"dummy": "test"}}
        result = ai_magics.display_output(output_text, "markdown", md)
        assert isinstance(result, Markdown)
        assert result.data == output_text
        bundle = result._repr_mimebundle_()
        assert bundle.get("text/markdown") == output_text

    def test_display_output_json_format(ai_magics):
        data = {"key": "value", "number": 42}
        json_string = json.dumps(data)
        md = {"jupyter_ai": {"dummy": "json"}}
        result = ai_magics.display_output(json_string, "json", md)
        assert isinstance(result, JSON)
        bundle = result._repr_mimebundle_()
        json_data = bundle.get("application/json") or bundle.get("text/json")
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        assert json_data == data 
