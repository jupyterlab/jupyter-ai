import os
from unittest.mock import Mock, patch

import pytest
from IPython import InteractiveShell
from IPython.core.display import Markdown
from jupyter_ai_magics.magics import AiMagics
from langchain_core.messages import AIMessage, HumanMessage
from pytest import fixture
from traitlets.config.loader import Config


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
    ip.run_line_magic("ai", "reset")
    assert ai_magics.transcript == []
