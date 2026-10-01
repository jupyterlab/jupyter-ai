# Tools and MCP servers

Agents in the chat act on your workspace through tools. Jupyter AI gives
every agent a set of notebook tools, and you can add tools from other MCP
servers.

## Notebook tools

By default, AI personas have access to the MCP server provided by the
`jupyter_server_mcp` package. Jupyter AI uses this to provide a notebook toolkit
to all AI personas by default.

These tools allow AI personas to:

- Answer questions about your active notebook or active cell
- Create and edit notebooks
- Run code cells through the kernel
- Open other files in JupyterLab

:::{tip}
The notebook tools are served by the Jupyter MCP server, which also accepts
connections from coding agents running in a terminal. See
{doc}`/users/terminal-agents/index`.
:::

## Custom MCP servers

You can share custom MCP servers to extend the capabilities of your AI personas
and tailor them to your workflow.

To add custom MCP servers, create a `.jupyter/mcp_settings.json` file at the root
of your workspace. This file contains an array of MCP server configurations
under `mcp_servers`. Jupyter AI reads this file on startup and makes the
configured servers available to all ACP agents automatically.

### Stdio servers

A stdio server runs as a local process. You specify the command and arguments
to launch it:

```json
{
  "mcp_servers": [
    {
      "name": "My Custom Tools",
      "command": "npx",
      "args": ["-y", "@my-org/my-mcp-server"],
      "env": [
        {"name": "API_KEY", "value": "sk-abc123"}
      ]
    }
  ]
}
```

| Field     | Type             | Required | Description                                          |
|-----------|------------------|----------|------------------------------------------------------|
| `name`    | string           | yes      | Human-readable name identifying this MCP server.     |
| `command` | string           | yes      | Path to the MCP server executable.                   |
| `args`    | list of strings  | yes      | Command-line arguments to pass to the server.        |
| `env`     | list of objects  | no       | Environment variables to set when launching. Each object has `name` and `value` fields. |

### HTTP servers

An HTTP server is a remote MCP server accessible over HTTP:

```json
{
  "mcp_servers": [
    {
      "type": "http",
      "name": "Remote Tools",
      "url": "https://my-mcp-server.example.com/mcp",
      "headers": [
        {"name": "Authorization", "value": "Bearer my-token"}
      ]
    }
  ]
}
```

| Field     | Type             | Required | Description                                          |
|-----------|------------------|----------|------------------------------------------------------|
| `type`    | `"http"`         | yes      | Must be `"http"` for HTTP servers.                   |
| `name`    | string           | yes      | Human-readable name identifying this MCP server.     |
| `url`     | string           | yes      | URL to the MCP server.                               |
| `headers` | list of objects  | no       | HTTP headers to include in requests. Each object has `name` and `value` fields. |

### Full example

Here is a complete `.jupyter/mcp_settings.json` with both server types:

```json
{
  "mcp_servers": [
    {
      "name": "Filesystem Tools",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    },
    {
      "name": "GitHub Tools",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": [
        {"name": "GITHUB_PERSONAL_ACCESS_TOKEN", "value": "ghp_xxx"}
      ]
    },
    {
      "type": "http",
      "name": "Company Internal Tools",
      "url": "https://internal-mcp.corp.example.com/mcp",
      "headers": [
        {"name": "Authorization", "value": "Bearer my-token"}
      ]
    }
  ]
}
```

After saving this file, restart JupyterLab for the changes to take effect. All
configured MCP servers will be available to every ACP agent in your session.
