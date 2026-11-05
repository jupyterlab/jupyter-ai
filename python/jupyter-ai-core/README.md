# jupyter-ai-core

JupyterLab with the extensions that let an AI agent work in it.

Use `jupyter-ai-core` when you run a coding agent, such as Claude Code, Codex,
GitHub Copilot CLI, Gemini CLI, or OpenCode, in a terminal next to JupyterLab.
The agent connects to the Jupyter MCP server, and can then open files, run
JupyterLab commands, and run notebook cells in your kernel.

```bash
pip install jupyter-ai-core
jupyter lab
```

Then register the Jupyter MCP server with your agent, for example with Claude
Code:

```bash
claude mcp add jupyter -- jupyter-server-mcp-proxy
```

## What gets installed

`jupyter-ai-core` is a meta-package. It installs:

- [`jupyterlab`](https://github.com/jupyterlab/jupyterlab)
- [`jupyter-server-mcp`](https://github.com/jupyter-ai-contrib/jupyter-server-mcp):
  an MCP server inside the Jupyter server, and the `jupyter-server-mcp-proxy`
  command that agents use to connect.
- [`jupyterlab-commands-toolkit`](https://github.com/jupyter-ai-contrib/jupyterlab-commands-toolkit):
  MCP tools that run JupyterLab commands in your browser tab.
- [`jupyter-live-content`](https://github.com/jupyter-ai-contrib/jupyter-live-content):
  reloads open files when the agent changes them on disk.

It also shows hidden files by default, so that you can see and edit agent
files such as `.mcp.json`, `.claude/`, and `.agents/`. It sets
`ContentsManager.allow_hidden` on the server, and `showHiddenFiles` in the
file browser. Your own settings take precedence.

For the agent chat in JupyterLab, install
[`jupyter-ai`](https://pypi.org/project/jupyter-ai/). It includes
`jupyter-ai-core`.

See the [Jupyter AI documentation](https://jupyter-ai.readthedocs.io) for more
information.
