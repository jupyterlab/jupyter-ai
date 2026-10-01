# Troubleshooting

This page covers common issues you may encounter when using Jupyter AI and how to resolve them.

## Terminal coding agents

### The agent does not show the `jupyter` server

Agents load their MCP servers when a session starts. Start a new session after
registering the server. Then check the list of servers, with `/mcp` in Claude
Code, Codex, or Gemini CLI.

If the server is listed but fails to start, run the command you registered in
the same terminal, for example `jupyter-server-mcp-proxy`. If the command is
not found, the agent runs outside the Jupyter environment: register the `uvx`
form instead (see {ref}`terminal-agents-where`).

### The proxy cannot find a Jupyter server

The proxy stops with this error:

```text
No running Jupyter MCP servers were discovered. Start Jupyter Server with the
jupyter-server-mcp extension, or pass --url / set $JUPYTER_SERVER_MCP_URL.
```

The proxy looks for running servers in the Jupyter runtime directory. Check
that:

- JupyterLab is running, and its log shows that the MCP server started.
- The agent was started in a folder that JupyterLab serves, when several
  servers are running. Otherwise the proxy stops with
  `Multiple Jupyter MCP servers are running and none contains the current
  working directory`, followed by the list of servers.
- JupyterLab and the proxy use the same runtime directory. If you set
  `JUPYTER_RUNTIME_DIR` for JupyterLab, pass the same directory to the proxy
  with `--runtime-dir`.

As a last resort, give the proxy the address of the MCP server with
`--url http://localhost:3001/mcp`, using the port shown in the JupyterLab log.

### The MCP server does not start because the port is in use

Another Jupyter server already uses port `3001`. Start JupyterLab with
`--MCPExtensionApp.mcp_port=0` to let the operating system pick a free port.
See {ref}`terminal-agents-several-servers`.

### The `jupyter` server is connected but has no tools

The proxy connects to a Jupyter server when the agent session starts. If
JupyterLab restarted since then, the proxy still points to the old server.
Reconnect the server from the agent, or start a new session.

### Tools wait and then fail

A tool returns `Command timed out after 10.0 seconds`. Tools that run
JupyterLab commands need a JupyterLab tab open in a browser, connected to the
same server. Open JupyterLab, or reload its tab, and try again.

### Commands run twice

Commands run in every JupyterLab tab connected to the server. Close the other
tabs, so that only one remains.

### An open notebook does not show the agent's changes

When an agent edits a notebook file on disk, the open notebook only updates
with real-time collaboration installed (see {doc}`/users/terminal-agents/setup`).
Without it, reload the notebook with **File → Reload Notebook from Disk**.

JupyterLab also does not reload documents with unsaved changes. Save your work
before asking the agent to edit an open file.

## Agent chat


### Persona does not appear in chat

Make sure you have installed the corresponding agent and its dependencies, and
that you are using the latest version. See the
{doc}`agent chat guide </users/chat/index>` for installation instructions.
Check the JupyterLab server logs for more information.

### Persona does not reply

You may not be authenticated with the agent's service. Try logging in through
the agent's CLI first, then restart JupyterLab. Some agents, like Goose or
OpenCode, will also require you to select an LLM before usage.

````{tabs}

```{tab} Claude

    claude login

```

```{tab} Codex

    codex

```

```{tab} GitHub Copilot

    copilot login

```

```{tab} Goose

    goose configure

```

```{tab} Kilo

    kilo auth login

```

```{tab} Kiro

    kiro-cli login

```

```{tab} Mistral Vibe

    vibe --setup

```

```{tab} OpenCode

    opencode auth login

```

````

For GitHub Copilot, you can also set `COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, or
`GITHUB_TOKEN` before starting JupyterLab instead of running `copilot login`.
For Mistral Vibe, you can also set `MISTRAL_API_KEY` before starting JupyterLab
instead of running `vibe --setup`.

If the error persists after logging in, check the server logs and
[open an issue](https://github.com/jupyterlab/jupyter-ai/issues/new/choose) on
GitHub.

### Persona does not request permission before running tools

Some agents default to not requesting tool call permissions. We make a best
effort to enforce safer defaults, but this is challenging to configure across
all agents and is still under active development. Refer to your agent's
documentation for setting up tool call permissions and approval policies.

### Updates to agent configuration do not take effect

You will need to restart the JupyterLab server for configuration changes to take
effect in all chats:

```
# Stop the running server (Ctrl+C), then restart:
jupyter lab
```

### Chats take a long time to load (orange spinner)

Wait a few seconds and try closing other browser tabs with JupyterLab open to
see if that helps. This is a known issue and we are working to address it.
