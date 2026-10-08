# Other projects

Jupyter's extension system makes it possible for anyone to add AI features to
JupyterLab and Jupyter Notebook, and many teams, companies, and universities
have done so. This documentation covers the projects developed under the
Jupyter AI umbrella. If they do not fit your needs, there are many more
options.

## Awesome Jupyter AI

[Awesome Jupyter AI](https://github.com/openteams-ai/awesome-jupyter-ai) is a
community-maintained list of more than a hundred AI extensions for JupyterLab
and Jupyter Notebook. It groups them by what they do:

- Chat panels and agents
- Inline code completion
- In-cell edits and magic commands
- Bridges to command-line agents such as Claude Code and Codex
- Extensions for teaching, specific domains, and platforms
- Building blocks: MCP servers, chat components, live reload

Each entry shows how recently the project was updated. A listing is not an
endorsement: check the license, the maintenance status, and where your data
goes before you install an extension.

## Building blocks

The Jupyter AI projects are made of small packages, developed in the
[`jupyter-ai-contrib`](https://github.com/jupyter-ai-contrib) organization,
that you can also use on their own:

| Package | What it does |
| --- | --- |
| [`jupyter-server-mcp`](https://github.com/jupyter-ai-contrib/jupyter-server-mcp) | Runs an MCP server inside the Jupyter server, and lets packages add tools to it. |
| [`jupyterlab-commands-toolkit`](https://github.com/jupyter-ai-contrib/jupyterlab-commands-toolkit) | Lets agents list and run JupyterLab commands. |
| [`jupyter-ai-tools`](https://github.com/jupyter-ai-contrib/jupyter-ai-tools) | Tools that read and edit notebooks. |
| [`jupyter-live-content`](https://github.com/jupyter-ai-contrib/jupyter-live-content) | Updates open documents when their file changes on disk, without real-time collaboration. |
| [`jupyterlab-chat`](https://github.com/jupyterlab/jupyter-chat) | The chat panel and chat files used by the agent chat. |
| [`jupyter-ai-acp-client`](https://github.com/jupyter-ai-contrib/jupyter-ai-acp-client) | Connects ACP agents to Jupyter chats. |
| [`nb-cli`](https://github.com/jupyter-ai-contrib/nb-cli) | A command-line tool to read and edit notebooks, designed for agents. |

The {doc}`contributor guide </contributors/index>` lists all the packages and
their status.
