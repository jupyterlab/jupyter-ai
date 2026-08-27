"""Server configuration for the jupyter-ai MCP web-client-routing E2E suite.

!! Never use this configuration in production because it opens the server to the
world and provides access to JupyterLab JavaScript objects through the global
window variable.
"""

import os
from pathlib import Path

from jupyterlab.galata import configure_jupyter_server

configure_jupyter_server(c)  # noqa: F821

# Fixture personas live under a hidden `.jupyter/personas/` directory, so the
# contents API must be allowed to create and serve hidden paths.
c.ContentsManager.allow_hidden = True  # noqa: F821
c.FileContentsManager.allow_hidden = True  # noqa: F821

# The fixture persona is the default, so a message routes to it without any
# persona-picker interaction (which is flaky to drive across two clients). The
# web_client_id is stamped on the message by the toolkit regardless of the
# picker, so routing is still exercised.
c.PersonaManager.default_persona_id = (  # noqa: F821
    "jupyter-ai-personas::mcp-notebook_persona::McpNotebookPersona"
)

# The vendored ACP personas (Kiro/Claude) that jupyter-ai-acp-client registers as
# entry points would otherwise load in every chat and pollute the deterministic
# fixture-only persona list. This env var makes them raise on import, which the
# PersonaManager treats as "skip".
os.environ["JUPYTER_AI_ACP_CLIENT_E2E_TESTING_ONLY"] = "1"

# The fixture personas locate their shared avatar asset via this env var.
os.environ["JAI_TEST_ASSETS_DIR"] = str(
    Path(__file__).parent.resolve() / "fixtures" / "assets"
)

# The HTTP port (--ServerApp.port) and the built-in MCP server port
# (--MCPExtensionApp.mcp_port) are passed on the `jlpm start` command line (see
# playwright.config.js); persona-manager reads the MCP port to build its
# built-in MCP server URL, so the fixture persona reaches jupyter-server-mcp.
