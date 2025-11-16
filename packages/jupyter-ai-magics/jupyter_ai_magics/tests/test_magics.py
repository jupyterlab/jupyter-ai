from unittest.mock import patch

from IPython import InteractiveShell
from jupyter_ai_magics.magics import AiMagics
from pytest import fixture
from traitlets.config.loader import Config


@fixture
def ip() -> InteractiveShell:
    ip = InteractiveShell()
    ip.config = Config()
    return ip


def test_aliases_config(ip):
    ip.config.AiMagics.initial_aliases = {
        "my_custom_alias": {
            "target": "my_provider:my_model",
            "api_base": None,
            "api_key_name": None
        }
    }
    ip.extension_manager.load_extension("jupyter_ai_magics")
    # Use 'list all' to see all models and aliases
    providers_list = ip.run_line_magic("ai", "list all")
    # Check that alias appears in the markdown output with correct format
    assert "### Aliases" in providers_list.markdown
    assert "* `my_custom_alias`:" in providers_list.markdown
    assert "  - target: `my_provider:my_model`" in providers_list.markdown


def test_default_model_cell(ip):
    ip.config.AiMagics.initial_language_model = "my-favourite-llm"
    ip.extension_manager.load_extension("jupyter_ai_magics")
    with patch.object(AiMagics, "run_ai_cell", return_value=None) as mock_run:
        ip.run_cell_magic("ai", "", cell="Write code for me please")
        assert mock_run.called
        cell_args = mock_run.call_args.args[0]
        assert cell_args.model_id == "my-favourite-llm"


def test_non_default_model_cell(ip):
    ip.config.AiMagics.initial_language_model = "my-favourite-llm"
    ip.extension_manager.load_extension("jupyter_ai_magics")
    with patch.object(AiMagics, "run_ai_cell", return_value=None) as mock_run:
        ip.run_cell_magic("ai", "some-different-llm", cell="Write code for me please")
        assert mock_run.called
        cell_args = mock_run.call_args.args[0]
        assert cell_args.model_id == "some-different-llm"


def test_default_model_error_line(ip):
    ip.config.AiMagics.initial_language_model = "my-favourite-llm"
    ip.extension_manager.load_extension("jupyter_ai_magics")
    with patch.object(AiMagics, "handle_fix", return_value=None) as mock_run:
        ip.run_cell_magic("ai", "fix", cell=None)
        assert mock_run.called
        cell_args = mock_run.call_args.args[0]
        assert cell_args.model_id == "my-favourite-llm"


def test_reset(ip):
    ip.extension_manager.load_extension("jupyter_ai_magics")
    ai_magics = ip.magics_manager.registry["AiMagics"]
    ai_magics.transcript = [{"role": "user", "content": "hello"}]
    ip.run_line_magic("ai", "reset")
    assert ai_magics.transcript == []


class DummyExecResult:
    def __init__(self, success=True, error_in_exec=None, error_before_exec=None):
        self.success = success
        self.error_in_exec = error_in_exec
        self.error_before_exec = error_before_exec


def test_error_handle_successful_cell(ip):
    ip.extension_manager.load_extension("jupyter_ai_magics")
    with patch.object(
        InteractiveShell, "run_cell", return_value=DummyExecResult(success=True)
    ) as mock_run_cell, patch.object(AiMagics, "run_ai_cell") as mock_ai_call:
        ip.run_cell_magic("ai", "--error-handle test-model", cell="print('ok')")
        assert mock_run_cell.called
        mock_ai_call.assert_not_called()


def test_error_handle_triggers_ai_on_failure(ip):
    ip.extension_manager.load_extension("jupyter_ai_magics")
    try:
        raise ValueError("boom")
    except ValueError as exc:
        error_exc = exc

    exec_result = DummyExecResult(success=False, error_in_exec=error_exc)
    with patch.object(InteractiveShell, "run_cell", return_value=exec_result), patch.object(
        AiMagics, "run_ai_cell", return_value=None
    ) as mock_ai_call:
        ip.run_cell_magic("ai", "--error-handle test-model", cell="1/0")
        mock_ai_call.assert_called_once()
        helper_args, prompt = mock_ai_call.call_args.args
        assert helper_args.error_handle is False
        normalized_prompt = prompt.replace("{{", "{").replace("}}", "}")
        assert "1/0" in normalized_prompt
        assert "ValueError" in normalized_prompt or "boom" in normalized_prompt
