from subprocess import PIPE, Popen
from typing import Optional

import pylspclient
from jupyter_ai import BaseProvider, TextField
from jupyter_ai import __version__ as jupyter_ai_version
from jupyter_ai_magics.models.completion import (
    InlineCompletionList,
    InlineCompletionReply,
    InlineCompletionRequest,
)
from jupyterlab import __version__ as jupyterlab_version

INIT_PARAMS = {
    "capabilities": {"workspace": {"workspaceFolders": False}},
    "initializationOptions": {
        "editorInfo": {"name": "JupyterLab", "version": jupyterlab_version},
        "editorPluginInfo": {"name": "jupyter-ai", "version": jupyter_ai_version},
    },
}


def calc_position_lineno_and_char(prefix, suffix):
    """
    Calculate the line number and character position within a text based on a given prefix and suffix text.
    GitHub Copilot LSP requires those positions for completion requests.
    https://www.npmjs.com/package/@github/copilot-language-server#panel-completions
    """

    full_text = prefix + suffix

    lineno = full_text.count("\n", 0, len(prefix))
    prefix_text = "\n".join(full_text.split("\n")[:lineno])
    char_pos = len(prefix) - len(prefix_text) - 1

    return lineno, char_pos


class GitHubCopilotLLM:
    process: Optional[Popen] = None

    def __init__(self, lsp_bin_path: str):
        self.lsp_bin_path = lsp_bin_path
        self.ensure_lsp_server_initialized()

    def _initialize(self):
        self.lsp_endpoint.call_method(method_name="initialize", **INIT_PARAMS)
        self.lsp_endpoint.send_notification(method_name="initialized")

    def _signin(self):
        self.ensure_lsp_server_initialized()
        res = self.lsp_endpoint.call_method(
            method_name="signIn",
        )
        return res

    def _signout(self):
        self.ensure_lsp_server_initialized()
        res = self.lsp_endpoint.call_method(
            method_name="signOut",
        )
        return res

    def _completion(self, code, pos_line, pos_char):
        self.ensure_lsp_server_initialized()
        self.lsp_endpoint.send_notification(
            method_name="textDocument/didOpen",
            **{
                "textDocument": {
                    "uri": "file:///dummy",
                    "version": 0,
                    "languageId": "python",
                    "text": code,
                }
            },
        )

        res = self.lsp_endpoint.call_method(
            method_name="textDocument/copilotPanelCompletion",
            **{
                "textDocument": {
                    "uri": "file:///dummy",
                    "version": 0,
                },
                "position": {
                    "line": pos_line,
                    "character": pos_char,
                },
            },
        )
        return res

    def _start_lsp_server(self):
        if not self.is_lsp_server_running:
            self.process = Popen(
                [self.lsp_bin_path, "--stdio"], stdin=PIPE, stdout=PIPE, stderr=PIPE
            )
            self.json_rpc_endpoint = pylspclient.JsonRpcEndpoint(
                self.process.stdin, self.process.stdout
            )
            self.lsp_endpoint = pylspclient.LspEndpoint(
                self.json_rpc_endpoint, timeout=15
            )
            self.lsp_endpoint.start()

    def _stop_lsp_server(self):
        self.lsp_endpoint.stop()
        self.process.kill()

    def ensure_lsp_server_initialized(self):
        if not self.is_lsp_server_running:
            self._start_lsp_server()
            self._initialize()

    @property
    def is_lsp_server_running(self):
        return self.process is not None and self.process.poll() is None

    @property
    def _llm_type(self) -> str:
        return "github-copilot"


class GitHubCopilotProvider(BaseProvider):
    id = "github-copilot"
    name = "GitHub Copilot"
    models = ["*"]
    model_id_key = "model"
    pypi_package_deps = ["pylspclient"]
    help = (
        "Make sure you've installed copilot-language-server [https://www.npmjs.com/package/@github/copilot-language-server](https://www.npmjs.com/package/@github/copilot-language-server) . "
        "Set this absolute path to `lsp_bin_path`."
    )
    fields = [
        TextField(
            key="lsp_bin_path", label="Copilot LSP binary absolute path", format="text"
        ),
    ]

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._llm = GitHubCopilotLLM(lsp_bin_path=self.lsp_bin_path)

    async def generate_inline_completions(self, request: InlineCompletionRequest):
        self._llm.ensure_lsp_server_initialized()

        full_text = request.prefix + request.suffix
        lineno, char = calc_position_lineno_and_char(request.prefix, request.suffix)
        suggestions = self._llm._completion(full_text, lineno, char)
        completions = [
            {
                "insertText": item["insertText"][char:],
            }
            for item in suggestions["items"]
        ]
        return InlineCompletionReply(
            list=InlineCompletionList(items=completions),
            reply_to=request.number,
        )
