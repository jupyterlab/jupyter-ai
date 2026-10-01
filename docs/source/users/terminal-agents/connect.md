# Connect your agent

To act on JupyterLab, the agent needs the Jupyter MCP server in its list of
MCP servers. You register the server once per agent, and the registration
keeps working across JupyterLab restarts, even when the MCP server gets a new
port.

## Register the Jupyter MCP server

Open a terminal in JupyterLab (**File → New → Terminal**) and run the command
for your agent. The commands register a server named `jupyter` that starts
`jupyter-server-mcp-proxy`. The proxy finds the running Jupyter server and
forwards the agent's requests to it.

::::{tab-set}

:::{tab-item} Claude Code
:sync: claude

```bash
claude mcp add --scope user jupyter -- jupyter-server-mcp-proxy
```

`--scope user` makes the server available in every project. Leave it out to
register the server for the current folder only.
:::

:::{tab-item} Codex
:sync: codex

```bash
codex mcp add jupyter -- jupyter-server-mcp-proxy
```

Codex saves the server in `~/.codex/config.toml`, for every project.
:::

:::{tab-item} GitHub Copilot CLI
:sync: copilot

Add the server to `~/.copilot/mcp-config.json`:

```json
{
  "mcpServers": {
    "jupyter": {
      "type": "local",
      "command": "jupyter-server-mcp-proxy",
      "args": [],
      "tools": ["*"]
    }
  }
}
```

You can also run `/mcp add` in an interactive Copilot CLI session.
:::

:::{tab-item} Gemini CLI
:sync: gemini

Add the server to `~/.gemini/settings.json`, or to `.gemini/settings.json` in
your project:

```json
{
  "mcpServers": {
    "jupyter": {
      "command": "jupyter-server-mcp-proxy"
    }
  }
}
```
:::

:::{tab-item} OpenCode
:sync: opencode

Add the server to `opencode.json` in your project, or to
`~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "jupyter": {
      "type": "local",
      "command": ["jupyter-server-mcp-proxy"],
      "enabled": true
    }
  }
}
```
:::

:::{tab-item} Other agents
:sync: other

Most agents accept a "stdio" MCP server in their configuration. Use
`jupyter-server-mcp-proxy` as the command, with no arguments. If the agent
only supports HTTP servers, see {ref}`terminal-agents-http`.
:::

::::

Then start a new agent session. Agents load their MCP servers when a session
starts, so a session that was already running does not see the new server.

:::{note}
The proxy connects to a Jupyter server when the agent session starts. If you
restart JupyterLab during a session, reconnect the `jupyter` server from the
agent (for example from the `/mcp` menu of Claude Code), or start a new
session.
:::

## Check the connection

1. Make sure JupyterLab is open in a browser tab. Most tools run in that tab,
   so they wait for it.
2. In the agent, list the MCP servers: `/mcp` in Claude Code, Codex, and
   Gemini CLI. The `jupyter` server should be connected.
3. Ask the agent to do something in JupyterLab, for example:

   > Open README.md in JupyterLab.

   > Create a notebook named `explore.ipynb` that loads `data.csv` with
   > pandas and plots the first column, then run all its cells.

(terminal-agents-where)=
## Where the agent can run

### In a JupyterLab terminal

This is the simplest option, and the one used in the commands above. A
JupyterLab terminal runs in the server's environment, so
`jupyter-server-mcp-proxy` is already on the `PATH`, and its working
directory is the folder JupyterLab serves.

It also works when JupyterLab runs on another machine, for example on a
JupyterHub or a cloud workstation: the agent runs on the same machine as the
Jupyter server, next to your files and kernels.

### In your own terminal

You can run the agent in any terminal on the same machine: a terminal app,
tmux, or the terminal of your editor. Two things to keep in mind:

- **Start the agent in a folder that JupyterLab serves**, such as the folder
  where you ran `jupyter lab` or one of its subfolders. When several Jupyter
  servers run, the proxy uses this folder to pick the right one.
- **The proxy may not be on the `PATH`** outside the Jupyter environment. Run
  it with [`uvx`](https://docs.astral.sh/uv/) instead, which works from any
  environment:

::::{tab-set}

:::{tab-item} Claude Code
:sync: claude

```bash
claude mcp add --scope user jupyter -- \
  uvx --from jupyter-server-mcp jupyter-server-mcp-proxy
```
:::

:::{tab-item} Codex
:sync: codex

```bash
codex mcp add jupyter -- \
  uvx --from jupyter-server-mcp jupyter-server-mcp-proxy
```
:::

:::{tab-item} GitHub Copilot CLI
:sync: copilot

```json
{
  "mcpServers": {
    "jupyter": {
      "type": "local",
      "command": "uvx",
      "args": ["--from", "jupyter-server-mcp", "jupyter-server-mcp-proxy"],
      "tools": ["*"]
    }
  }
}
```
:::

:::{tab-item} Gemini CLI
:sync: gemini

```json
{
  "mcpServers": {
    "jupyter": {
      "command": "uvx",
      "args": ["--from", "jupyter-server-mcp", "jupyter-server-mcp-proxy"]
    }
  }
}
```
:::

:::{tab-item} OpenCode
:sync: opencode

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "jupyter": {
      "type": "local",
      "command": ["uvx", "--from", "jupyter-server-mcp", "jupyter-server-mcp-proxy"],
      "enabled": true
    }
  }
}
```
:::

:::{tab-item} Other agents
:sync: other

Use `uvx` as the command, with the arguments
`--from jupyter-server-mcp jupyter-server-mcp-proxy`.
:::

::::

The `uvx` form works in a JupyterLab terminal too, so you can use it
everywhere if you prefer a single registration.

The proxy finds running servers through the files that Jupyter writes in its
runtime directory (shown by `jupyter --runtime-dir`). If you start JupyterLab
with a custom `JUPYTER_RUNTIME_DIR`, give the same directory to the proxy with
`--runtime-dir`.

### In a desktop app

Some agents also come as desktop apps or editor extensions, such as Claude
Code in the Claude desktop app or the Codex extension for VS Code. They can
use the Jupyter MCP server like the command-line agent does:

- Add the server to the app's MCP configuration with the `uvx` command above.
  Apps that run the same agent as the command line usually read the same
  configuration files, so a server registered for every project (for example
  with `claude mcp add --scope user`) is often available there already.
- Open the same project folder in the app as the one JupyterLab serves.
- Keep JupyterLab open in a browser tab next to the app.

(terminal-agents-several-servers)=
## Several Jupyter servers

When you run several Jupyter servers at the same time, start each one with
`--MCPExtensionApp.mcp_port=0` so that each MCP server gets its own free port
(see {doc}`setup`). The proxy then connects to the server whose root folder is
the closest parent of the agent's working directory.

If no server serves the agent's working directory, or if two servers serve the
same folder, the proxy stops with an error rather than guess, and lists the
running servers. In that case, give it the server's URL with the `--url`
option, for example `--url http://localhost:3001/mcp`. The JupyterLab log
shows the port when the MCP server starts: `MCP server started on port 3001`.
With a single Jupyter server, the proxy always connects to it, wherever the
agent runs.

(terminal-agents-http)=
## Connect over HTTP

Instead of the proxy, an agent can connect to the MCP server's HTTP endpoint,
`http://localhost:3001/mcp` by default. This needs a fixed port, so it only
suits a single Jupyter server.

::::{tab-set}

:::{tab-item} Claude Code
:sync: claude

```bash
claude mcp add --transport http jupyter http://localhost:3001/mcp
```
:::

:::{tab-item} Codex
:sync: codex

```bash
codex mcp add jupyter --url http://localhost:3001/mcp
```
:::

:::{tab-item} Mistral Vibe
:sync: vibe

Add the server to `./.vibe/config.toml` or `~/.vibe/config.toml`:

```toml
[[mcp_servers]]
name = "jupyter"
transport = "streamable-http"
url = "http://localhost:3001/mcp"
```
:::

:::{tab-item} Other agents
:sync: other

Choose the "HTTP" or "Streamable HTTP" transport, with the URL
`http://localhost:3001/mcp`.
:::

::::

The [`jupyter-server-mcp` documentation](https://github.com/jupyter-ai-contrib/jupyter-server-mcp)
has more client configurations.

## Security

:::{warning}
The MCP server gives the agent the same power as you have in JupyterLab,
including running code in your kernels. It runs on its own port, outside the
token authentication of the Jupyter server.

The server only listens on the local loopback interface, and it rejects
requests from other websites. Any program running on the same machine can
still connect to it. Do not run it on a machine that you share with other
users unless you trust them, and do not expose the port to the network.
:::

Agents ask for permission before they use a tool, unless you allow it. Review
which tools you allow without asking, especially `execute_command`, which can
run any JupyterLab command.
