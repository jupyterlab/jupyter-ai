"""Fixture persona for the ``mcp`` E2E suite: exercises the full web-client
command-routing chain end to end.

Contract
--------
On each message, this persona reads the message body as JSON describing a
notebook to build and run, for example::

    {"notebook": "test.ipynb", "cells": ["x = 0\\nprint(x)"]}

It then, over MCP, asks the built-in Jupyter MCP server (``jupyter-server-mcp``)
to run a single JupyterLab frontend command, ``e2e:build-notebook``, with those
args. That command (registered by the test in each browser) creates the notebook
at ``notebook``, adds each string in ``cells`` as a code cell, opens it, and runs
the whole notebook.

Why this is a real end-to-end test
----------------------------------
The persona is the MCP client (standing in for an ACP agent). It builds the MCP
connection from ``get_mcp_settings()`` — the exact config the ACP client hands a
real agent — which carries the identity headers persona-manager stamps
(``X-Jupyter-Chat-Id``, ``X-JupyterAI-Persona-Id``). ``jupyter-server-mcp``'s
middleware reads those headers, looks this persona up, reads the
``web_client_id`` off the message it is currently processing, and publishes it so
``jupyterlab-commands-toolkit`` stamps the emitted ``lab_command`` event. Only
the browser tab whose ``web_client_id`` matches runs the command. So a command
triggered by one web client's message builds a notebook only in that client's
browser — never in another client's, which is the bug this guards against
(jupyterlab/jupyter-ai#1650).

This fixture is only installed by the ``mcp`` suite, whose env has ``mcp`` and
``fastmcp`` available.
"""

import json
import os

from jupyter_ai_persona_manager import BasePersona, McpServerHttp, PersonaDefaults
from jupyterlab_chat.models import Message
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

_AVATAR_PATH = os.path.join(os.environ["JAI_TEST_ASSETS_DIR"], "persona.svg")


class McpNotebookPersona(BasePersona):
    """Builds and runs a notebook on the requesting web client, via MCP."""

    @property
    def defaults(self) -> PersonaDefaults:
        return PersonaDefaults(
            name="MCP Notebook Persona",
            description="Builds and runs a notebook from a JSON message, via MCP.",
            avatar_path=_AVATAR_PATH,
            system_prompt="unused",
        )

    async def process_message(self, message: Message) -> None:
        spec = json.loads(message.body)

        # Build the MCP connection exactly as the ACP client would for an agent:
        # the built-in Jupyter MCP server, carrying our identity headers.
        settings = self.get_mcp_settings()
        server = next(
            s for s in settings.mcp_servers if isinstance(s, McpServerHttp)
        )
        headers = {header.name: header.value for header in server.headers}

        async with (
            streamablehttp_client(server.url, headers=headers) as (read, write, _),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            await session.call_tool(
                "execute_command",
                {
                    "command_id": "e2e:build-notebook",
                    "args": {
                        "path": spec["notebook"],
                        "cells": spec["cells"],
                    },
                },
            )

        self.send_message(f"Built {spec['notebook']}.")
