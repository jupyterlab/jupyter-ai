# Work with an agent

Once the agent is connected, you work with it as usual, in its own interface.
This page covers what it can do in JupyterLab, and the habits that make the
collaboration smooth.

## What the agent can do in JupyterLab

With the setup from {doc}`setup`, the Jupyter MCP server offers these tools:

| Tool | What it does |
| --- | --- |
| `list_all_commands` | Lists the JupyterLab commands available in your browser tab, with their arguments. Takes an optional search text. |
| `execute_command` | Runs a JupyterLab command with arguments, and returns its result. |

JupyterLab commands are the actions behind every menu item, button, and
keyboard shortcut, and extensions add their own. With these two tools, the
agent can do nearly anything you can do in the interface. A few examples:

| Command | What it does |
| --- | --- |
| `docmanager:open` | Opens a file, with the `path` argument. |
| `notebook:run-all-cells` | Runs all the cells of the active notebook. |
| `notebook:restart-run-all` | Restarts the kernel and runs all the cells. |
| `notebook:run-cell` | Runs the selected cells, without moving to the next cell. |
| `terminal:create-new` | Opens a new terminal. |
| `filebrowser:go-to-path` | Shows a folder in the file browser. |

Other packages can add more tools, and you can write your own (see
{doc}`/developers/agent-tools`). For example, the `jupyter-ai` package adds
tools that work on notebook cells:

| Purpose | Tools |
| --- | --- |
| Read | `read_notebook`, `read_notebook_cells`, `read_cell`, `get_active_notebook`, `get_active_cell_id`, `get_cell_id_from_index` |
| Edit | `create_notebook`, `add_cell`, `insert_cell`, `edit_cell`, `delete_cell`, `select_cell` |
| Run | `open_file`, `run_cell`, `run_all_cells` |

:::{note}
Most tools run in your JupyterLab browser tab, so they need one to be open.
By default, a command runs in **every** open JupyterLab tab of the server.
Keep a single JupyterLab tab open per server to avoid running cells twice.
:::

## Notebooks

An agent can change a notebook in two ways, and each has its strengths.

**Edit the file on disk.** The agent edits the `.ipynb` file with its own
tools, as it does for any other file. This is fast, and the changes show up
in your version control like any other edit. With RTC installed (see
{doc}`setup`), the open notebook updates in place, and keeps its outputs and
its kernel. The agent cannot run the cells this way, and only sees the
outputs that were saved to the file.

**Drive JupyterLab.** The agent opens the notebook and runs its cells through
JupyterLab commands. The code runs in the notebook's kernel, so it shares its
variables with you, and you watch the outputs appear. This is the way to run
code that needs the state of your session, for example a dataframe you
loaded earlier.

A good split is to keep reusable code in Python modules that the agent edits
on disk, and to use notebooks for exploration and results that the agent runs
through JupyterLab.

:::{tip}
Save your open documents before you ask the agent to edit them. JupyterLab
does not reload a document with unsaved changes, so that your edits are never
lost.
:::

## Give the agent instructions

Agents read a file of project instructions at the start of each session:
`AGENTS.md` for most agents, `CLAUDE.md` for Claude Code, and `GEMINI.md` for
Gemini CLI. Use it to tell the agent how you want it to work with JupyterLab.
For example:

```markdown
## JupyterLab

JupyterLab is open for this project. Use the `jupyter` MCP server to work with it.

- When you create or change a file I should look at, open it in JupyterLab
  with the `docmanager:open` command.
- To run a notebook, open it, then run `notebook:run-all-cells`. Read the
  outputs and fix any error before you report back.
- Do not restart kernels without asking me first.
```

[Agent Skills](https://agentskills.io) go further: they package
instructions, scripts, and references that the agent loads when a task needs
them. Most coding agents support them. See {doc}`examples` for skills written
for JupyterLab.

## Review the changes

An agent can change many files quickly, so make reviewing them part of the
loop:

- Install [`jupyterlab-git`](https://github.com/jupyterlab/jupyterlab-git) to
  see what changed in the **Git** panel, with diffs for text files and for
  notebooks.
- Ask the agent to commit at good checkpoints, so that you can always go back.
- Open the diff of a notebook rather than the raw JSON: notebook diffs show
  the changed cells and outputs side by side.

## Tips

- **One environment for the agent and the kernel.** The agent runs shell
  commands in the environment of its terminal, while notebooks run in their
  kernel. When both use the same environment, packages the agent installs are
  available to your notebooks.
- **Keep JupyterLab open.** Tools that run in the browser wait for a
  JupyterLab tab. If no tab is open, they fail after 10 seconds. Without RTC,
  this includes the notebook tools of the `jupyter-ai` package, even those
  that only read a notebook.
- **Use more than one agent.** Each agent runs in its own terminal, and all
  of them can connect to the same Jupyter server.
- **Read the server log** when something does not work. The terminal where
  you started JupyterLab shows the MCP server's port and the tools it
  registered.
