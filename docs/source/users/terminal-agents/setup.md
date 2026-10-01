# Set up JupyterLab

This page shows how to install JupyterLab with the extensions a terminal agent
needs, and the settings that make day-to-day work smoother.

## Install

The quickest way is [`ajlab`](https://github.com/jtpio/ajlab), a small
package that installs JupyterLab with the extensions listed below and a few
defaults for agent workflows.

````{tabs}

```{tab} pip

    pip install ajlab

```

```{tab} uv

    uv pip install ajlab

```

```{tab} uv tool

    # installs JupyterLab and the extensions in their own environment,
    # with jupyter-lab and jupyter-server-mcp-proxy on your PATH
    uv tool install jupyterlab --with ajlab --with-executables-from jupyter-server-mcp

```

```{tab} uvx

    # runs JupyterLab without installing anything permanently
    uvx --from ajlab jupyter-lab

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

`ajlab` is a meta-package: it has no code of its own. You can install the
same packages yourself, or add them to an existing environment.

| Package | What it does |
| --- | --- |
| [`jupyterlab`](https://github.com/jupyterlab/jupyterlab) | The JupyterLab application, version 4.6 or later. |
| [`jupyter-server-mcp`](https://github.com/jupyter-ai-contrib/jupyter-server-mcp) | Runs an MCP server inside the Jupyter server and provides the `jupyter-server-mcp-proxy` command that agents use to connect. |
| [`jupyterlab-commands-toolkit`](https://github.com/jupyter-ai-contrib/jupyterlab-commands-toolkit) | Adds two MCP tools, `list_all_commands` and `execute_command`, which let the agent run any JupyterLab command in your browser tab. |
| [`jupyter-server-ydoc`](https://github.com/jupyterlab/jupyter-collaboration) and [`jupyter-docprovider`](https://github.com/jupyterlab/jupyter-collaboration) | The real-time collaboration (RTC) document server and its JupyterLab provider. When the agent edits a file on disk, the open document updates in place. This includes notebooks. |

```bash
pip install jupyterlab jupyter-server-mcp jupyterlab-commands-toolkit jupyter-server-ydoc jupyter-docprovider
```

`jupyter-server-ydoc` and `jupyter-docprovider` are two of the packages that
make up [Jupyter Collaboration](https://jupyterlab-realtime-collaboration.readthedocs.io).
Installing them on their own gives live updates without the rest of the
collaboration interface. You can also install `jupyter-collaboration`
instead, which adds that interface: shared cursors, the list of
collaborators, and the document timeline.

### Live updates without RTC

If you prefer not to use RTC, install
[`jupyter-live-content`](https://github.com/jupyter-ai-contrib/jupyter-live-content)
instead of `jupyter-server-ydoc` and `jupyter-docprovider`. It reloads open
text files, Markdown previews, and images when they change on disk. It does
**not** reload notebooks: an open notebook keeps showing its old content
until you reload it with **File → Reload Notebook from Disk**.

| | Text files | Notebooks | Notes |
| --- | --- | --- | --- |
| RTC (`jupyter-server-ydoc` and `jupyter-docprovider`) | Live | Live | Outputs and the kernel are kept. |
| `jupyter-live-content` | Live | Not updated | Turns itself off when RTC is installed. |
| Neither | Not updated | Not updated | JupyterLab warns about the conflict when you save. |

## Recommended settings

`ajlab` changes two defaults. If you install the packages yourself, you can
apply the same settings.

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
`jupyter-server-mcp` and `jupyterlab-commands-toolkit`, and adds notebook
tools to the same MCP server. A terminal agent can connect to it as described
in {doc}`connect`, and use the same tools as the agents in the chat.

For live updates of notebooks edited on disk, install one of the RTC options
of `jupyter-ai`, for example `pip install "jupyter-ai[rtc]"`. Without RTC, the
notebook tools of `jupyter-ai` work through your JupyterLab tab, so they need
one to be open.

## Next step

{doc}`connect`.
