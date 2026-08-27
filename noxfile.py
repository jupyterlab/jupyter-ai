# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""E2E test matrix for jupyter-ai.

Runs the Playwright/galata ui-tests suite under three transports so the
web-client command-routing chain is exercised end-to-end in every supported
mode:

    - default   -- RTC-free, WebSocket ``WsChatModel``
    - rtc       -- RTC via ``jupyter_collaboration``
    - rtc-jsd   -- RTC via ``jupyter_server_documents``

Each session builds an isolated venv (uv) and installs jupyter-ai -- the
prebuilt wheel via ``E2E_WHEEL`` in CI, or from source locally -- plus the
transport's packages and the MCP client deps the fixture persona uses.

Usage::

    nox -l                          # list sessions
    nox -s e2e                      # all three transports
    nox -s "e2e(env='rtc')"         # one transport
"""

import os

import nox

nox.options.default_venv_backend = "uv|virtualenv"

# env name -> extra packages that provide the transport.
_ENVS = {
    "default": [],
    "rtc": ["jupyter_collaboration>=4,<5"],
    "rtc-jsd": ["jupyter_server_documents"],
}


@nox.session(python="3.11")
@nox.parametrize("env", list(_ENVS))
def e2e(session: nox.Session, env: str) -> None:
    """Run the ui-tests suite against one transport."""
    # The prebuilt wheel from CI; from source for local runs.
    target = os.environ.get("E2E_WHEEL") or "."
    # `fastmcp`/`mcp` back the fixture persona's MCP client.
    session.install("jupyterlab>=4.4,<5", "fastmcp", "mcp", target, *_ENVS[env])
    session.env["E2E_RTC"] = "1" if env in ("rtc", "rtc-jsd") else "0"
    with session.chdir("ui-tests"):
        session.run("jlpm", "install", external=True)
        session.run("jlpm", "playwright", "install", "chromium", external=True)
        session.run("jlpm", "playwright", "test", external=True)
