<p align="center">
  <img src="docs/source/_static/jupyter_logo.png" alt="Jupyter logo" width="120">
</p>

<h1 align="center">Jupyter AI</h1>

<p align="center"><i>An open source extension that connects AI agents to computational notebooks in JupyterLab.</i></p>

Jupyter AI brings agentic AI to JupyterLab. It provides a native chat UI where you can collaborate with frontier AI agents — including Claude, Codex, GitHub Copilot, Gemini, Goose, Kiro, Mistral Vibe, and OpenCode — all integrated through the [Agent Client Protocol (ACP)](https://agentclientprotocol.com). Agents are automatically detected when their dependencies are installed, so getting started is as simple as installing Jupyter AI and the agent of your choice.

Agents in Jupyter AI can read and write files, run terminal commands, and interact with notebooks through a built-in [Jupyter MCP server](https://github.com/jupyter-ai-contrib/jupyter-server-mcp). A permission system gives you guardrails over agent actions — agents request approval before writing files or executing commands. You can also create multiple concurrent chats, drag and drop files or notebook cells as context, and collaborate in real time with other users connected to the same server.

Jupyter AI is designed to be flexible and extensible. You can add custom [MCP servers](https://modelcontextprotocol.io) to give agents access to domain-specific tools, resources, and prompts. Developers can build and register their own AI personas using the entry points API. By building on open standards like ACP and MCP, Jupyter AI avoids vendor lock-in and gives you access to the full ecosystem of compatible agents and tools.

## Quick Links

- [Getting Started](https://jupyter-ai.readthedocs.io/en/latest/getting-started.html) — installation, agent setup, and first chat
- [User Guide](https://jupyter-ai.readthedocs.io/en/latest/users/index.html) — chat features, notebook tools, and custom MCP servers
- [Contributor Guide](https://jupyter-ai.readthedocs.io/en/latest/contributors/index.html) — how to contribute to Jupyter AI
- [Developer Guide](https://jupyter-ai.readthedocs.io/en/latest/developers/index.html) — building custom agents and MCP servers
- [Troubleshooting](https://jupyter-ai.readthedocs.io/en/latest/users/troubleshooting.html) — common issues and solutions

## Governance

Jupyter AI is currently under incubation as part of the JupyterLab organization.
