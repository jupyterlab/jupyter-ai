# Add tools for agents

Agents in Jupyter use two kinds of tools: Python functions served by the
Jupyter MCP server, and JupyterLab commands. A package that adds either one
gives a new capability to every agent: terminal coding agents, agents in the
agent chat, and, for commands, Jupyternaut in the browser.

| | Python tool | JupyterLab command |
| --- | --- | --- |
| Runs in | The Jupyter server process | The user's browser tab |
| Good for | Files, the server's environment, external services | The user interface, open documents, kernels of open notebooks |
| Available to | Terminal agents and the agent chat, through MCP | Terminal agents and the agent chat through `execute_command`, and Jupyternaut in the browser |
| Works in JupyterLite | No | Yes |

## Add a Python tool to the Jupyter MCP server

The [`jupyter-server-mcp`](https://github.com/jupyter-ai-contrib/jupyter-server-mcp)
package turns Python functions into MCP tools. The function name becomes the
tool name, the docstring its description, and the type hints its input
schema. Functions can be synchronous or `async`.

```python
# my_package/tools.py

def word_count(path: str) -> int:
    """Count the words in a text file of the workspace."""
    with open(path, encoding="utf-8") as f:
        return len(f.read().split())

TOOLS = [
    "my_package.tools:word_count",
]
```

Declare the list in the `jupyter_server_mcp.tools` entry point group of your
package, and the MCP server registers the tools when it starts:

```toml
# pyproject.toml
[project.entry-points."jupyter_server_mcp.tools"]
my_package = "my_package.tools:TOOLS"
```

Users can also register any importable function in their Jupyter
configuration, without an entry point:

```python
# jupyter_server_config.py
c.MCPExtensionApp.mcp_tools = [
    "my_package.tools:word_count",
]
```

The `jupyter-server-mcp` documentation also covers MCP middleware, which runs
around every request, and the other configuration options.

## Add a JupyterLab command

Any command that a JupyterLab extension registers can be run by agents: with
the `execute_command` tool from
[`jupyterlab-commands-toolkit`](https://github.com/jupyter-ai-contrib/jupyterlab-commands-toolkit),
or directly by Jupyternaut in the browser. Agents discover commands with
`list_all_commands`, which returns the ID, label, caption, and argument schema
of each one.

Make a command easy for an agent to use:

- Give it a **clear label and caption**, which explain what it does and when
  to use it.
- Describe its **arguments with a JSON schema** in `describedBy`, including a
  description of each argument.
- **Return a JSON-serializable result**, so that the agent can read it.
  `execute_command` returns the result to the agent, or the error message if
  the command fails.

```typescript
app.commands.addCommand('my-extension:count-cells', {
  label: 'Count Notebook Cells',
  caption: 'Count the code and Markdown cells of the active notebook',
  describedBy: {
    args: {
      type: 'object',
      properties: {
        cellType: {
          type: 'string',
          enum: ['code', 'markdown'],
          description: 'Only count the cells of this type'
        }
      }
    }
  },
  execute: args => {
    const notebook = tracker.currentWidget?.content;
    if (!notebook) {
      throw new Error('No active notebook');
    }
    const cells = notebook.widgets.filter(
      cell => !args.cellType || cell.model.type === args.cellType
    );
    return { count: cells.length };
  }
});
```

## Add an AI persona

To add a new persona to the agent chat, for example one that wraps your own
agent, see the {doc}`entry points API <entry_points_api/index>`.
