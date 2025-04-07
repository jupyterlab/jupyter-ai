import unittest
from subprocess import PIPE
from unittest.mock import MagicMock, patch

from jupyter_ai_magics.models.completion import InlineCompletionRequest
from jupyter_ai_magics.partner_providers.copilot import (
    GitHubCopilotLLM,
    GitHubCopilotProvider,
    calc_position_lineno_and_char,
)


class TestGitHubCopilotLLM(unittest.TestCase):
    @patch("jupyter_ai_magics.partner_providers.copilot.Popen")
    @patch("jupyter_ai_magics.partner_providers.copilot.pylspclient.JsonRpcEndpoint")
    @patch("jupyter_ai_magics.partner_providers.copilot.pylspclient.LspEndpoint")
    def test_initialize_lsp_server(
        self, mock_lsp_endpoint, mock_json_rpc_endpoint, mock_popen
    ):
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        mock_endpoint = MagicMock()
        mock_lsp_endpoint.return_value = mock_endpoint

        llm = GitHubCopilotLLM(lsp_bin_path="dummy_path")

        mock_popen.assert_called_once_with(
            ["dummy_path", "--stdio"], stdin=PIPE, stdout=PIPE, stderr=PIPE
        )
        mock_json_rpc_endpoint.assert_called_once_with(
            mock_process.stdin, mock_process.stdout
        )
        mock_lsp_endpoint.assert_called_once_with(
            mock_json_rpc_endpoint.return_value, timeout=15
        )
        mock_endpoint.start.assert_called_once()

    def test_calc_position_lineno_and_char(self):
        prefix = "line1\nline2\n"
        suffix = "line3\nline4"
        lineno, char_pos = calc_position_lineno_and_char(prefix, suffix)

        self.assertEqual(lineno, 2)
        self.assertEqual(char_pos, 0)


class TestGitHubCopilotProvider(unittest.TestCase):
    @patch("jupyter_ai_magics.partner_providers.copilot.GitHubCopilotLLM")
    def test_generate_inline_completions(self, mock_llm_class):
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        mock_llm._completion.return_value = {
            "items": [{"insertText": "completion1"}, {"insertText": "completion2"}]
        }

        provider = GitHubCopilotProvider(
            lsp_bin_path="dummy_path", model_id="github-copilot"
        )
        result = provider._llm._completion("print()", 0, 6)

        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["insertText"], "completion1")
        self.assertEqual(result["items"][1]["insertText"], "completion2")


if __name__ == "__main__":
    unittest.main()
