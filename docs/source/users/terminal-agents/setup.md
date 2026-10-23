# Set up JupyterLab

This page shows how to install JupyterLab with the extensions a terminal agent
needs, and the settings that make day-to-day work smoother.

## Install

The quickest way is `jupyter-ai-core`, a small package that installs
JupyterLab with the extensions listed below and a few defaults for agent
workflows.

````{tabs}

```{tab} pip

    pip install jupyter-ai-core

```

```{tab} uv

    uv pip install jupyter-ai-core

```

```{tab} uv tool

    # installs JupyterLab and the extensions in their own environment,
    # with jupyter-lab and jupyter-server-mcp-proxy on your PATH
    uv tool install jupyterlab --with jupyter-ai-core --with-executables-from jupyter-server-mcp

```

```{tab} uvx

    # runs JupyterLab without installing anything permanently
    uvx --from jupyter-ai-core jupyter-lab

```

````

Then start JupyterLab from your project folder:

```bash
cd my-project
jupyter lab
```

:::{tip}
Install JupyterLab in the same environment as your project's dependencies
when you want notebooks to use them. The kernel then runs in that environment,
and so does the shell of each JupyterLab terminal. With `uv tool` or `uvx`,
JupyterLab runs in its own environment: install a kernel for your project's
environment to use its packages in notebooks.
:::

## What gets installed

`jupyter-ai-core` is a meta-package: it has no code of its own. You can install
the same packages yourself, or add them to an existing environment.

| Package | What it does |
| --- | --- |
| [`jupyterlab`](https://github.com/jupyterlab/jupyterlab) | The JupyterLab application. |
| [`jupyter-server-mcp`](https://github.com/jupyter-ai-contrib/jupyter-server-mcp) | Runs an MCP server inside the Jupyter server and provides the `jupyter-server-mcp-proxy` command that agents use to connect. |
| [`jupyterlab-commands-toolkit`](https://github.com/jupyter-ai-contrib/jupyterlab-commands-toolkit) | Adds two MCP tools, `list_all_commands` and `execute_command`, which let the agent run any JupyterLab command in your browser tab. |
| [`jupyter-live-content`](https://github.com/jupyter-ai-contrib/jupyter-live-content) | Reloads open text files, Markdown previews, and images when the agent changes them on disk. |

```bash
pip install jupyterlab jupyter-server-mcp jupyterlab-commands-toolkit jupyter-live-content
```

(terminal-agents-live-notebooks)=
### Live updates for notebooks

`jupyter-live-content` does not reload notebooks, so that it never discards
outputs or state that only exist in your browser. When the agent edits a
notebook file on disk, the open notebook keeps showing its old content until
you reload it with **File → Reload Notebook from Disk**.

There are two ways to see an agent's notebook changes live:

- **Let the agent change the notebook through JupyterLab**, with JupyterLab
  commands or the notebook tools of the `jupyter-ai` package. The change
  happens in the open notebook. See {ref}`terminal-agents-notebooks`.
- **Add real-time collaboration (RTC).** RTC keeps a shared copy of each open
  document on the server, and updates open notebooks in place when they
  change on disk, without losing outputs or the kernel:

  ```bash
  pip install jupyter-server-ydoc jupyter-docprovider
  ```

  These two packages are the parts of
  [Jupyter Collaboration](https://jupyterlab-realtime-collaboration.readthedocs.io)
  that provide live updates. Install `jupyter-collaboration` instead to also
  get the collaboration interface: shared cursors, the list of collaborators,
  and the document timeline.

| | Text files | Notebooks | Notes |
| --- | --- | --- | --- |
| `jupyter-live-content`, included in `jupyter-ai-core` | Live | Not updated | Turns itself off when RTC is installed. |
| RTC (`jupyter-server-ydoc` and `jupyter-docprovider`) | Live | Live | Outputs and the kernel are kept. |
| Neither | Not updated | Not updated | JupyterLab warns about the conflict when you save. |

## Recommended settings

`jupyter-ai-core` changes two defaults. If you install the packages yourself,
you can apply the same settings.

### Show hidden files

Agents keep their configuration and instructions in files and folders whose
names start with a dot: `.mcp.json`, `.claude/`, `.codex/`, and
`.agents/skills/`. To see and edit them in JupyterLab, allow the server to
serve hidden files and show them in the file browser.

Allow hidden files on the server, in `jupyter_server_config.json` in one of
the `config` directories listed by `jupyter --paths`:

```json
{
  "ContentsManager": {
    "allow_hidden": true
  }
}
```

Then show them in the file browser: select **View → Show Hidden Files**, or
set `showHiddenFiles` to `true` for the **File Browser** in the Settings
Editor.

To ship both settings as defaults for everyone using an environment, see
{ref}`terminal-agents-own-distribution`.

### Choose the MCP port

The MCP server listens on port `3001` by default. If that port is in use, for
example by another Jupyter server, JupyterLab still starts, but its MCP server
does not: the log shows an error, and the proxy connects the agent to the
other server instead.

To run several Jupyter servers side by side, let the operating system pick a
free port for each one. The proxy finds the right server by itself (see
{ref}`terminal-agents-several-servers`).

```bash
jupyter lab --MCPExtensionApp.mcp_port=0
```

To make this the default, add it to `jupyter_server_config.py`:

```python
c.MCPExtensionApp.mcp_port = 0
```

## Already using the Jupyter AI package?

The `jupyter-ai` package (see {doc}`/users/chat/index`) already includes
`jupyter-server-mcp`, `jupyterlab-commands-toolkit`, and
`jupyter-live-content`, and adds notebook tools to the same MCP server. A terminal agent can connect to it as described
in {doc}`connect`, and use the same tools as the agents in the chat.

For live updates of notebooks edited on disk, install one of the RTC options
of `jupyter-ai`, for example `pip install "jupyter-ai[rtc]"`. Without RTC, the
notebook tools of `jupyter-ai` work through your JupyterLab tab, so they need
one to be open.

## Next step

{doc}`connect`.
