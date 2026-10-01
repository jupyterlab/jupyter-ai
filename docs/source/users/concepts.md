# How it fits together

All the ways to use AI in Jupyter rely on a few shared ideas and packages.
Knowing them helps you choose a setup, configure it, and understand what an
agent can do.

```{mermaid}
flowchart LR
    term["Terminal coding agent<br/>Claude Code, Codex, ..."]
    acp["Agents in the agent chat<br/>started by Jupyter AI"]
    browser["Jupyternaut<br/>in the browser"]
    mcp["Jupyter MCP server<br/>jupyter-server-mcp"]
    lab["JupyterLab<br/>commands and open documents"]
    term -- "MCP" --> mcp
    acp -- "MCP" --> mcp
    mcp -- "JupyterLab commands" --> lab
    browser -- "JupyterLab commands" --> lab
```

Agents also read and write files. With live updates (see
{ref}`concepts-live-updates`), JupyterLab shows their changes in the open
documents.

## Agents, models, and personas

- A **model** is the large language model that generates text, such as
  Claude Sonnet, GPT, or Gemini.
- An **agent** is the program around the model. It keeps the conversation,
  calls tools such as "read a file" or "run a command", and decides what to do
  next. Claude Code, Codex CLI, and Gemini CLI are agents.
- A **persona** is how an agent appears in a Jupyter chat: a name and an
  avatar that you can mention, and that replies to your messages. In the
  agent chat, each installed agent becomes a persona.

## Tools and the Model Context Protocol

Agents act on the world through **tools**. The
[Model Context Protocol (MCP)](https://modelcontextprotocol.io) is the open
standard that lets any agent use tools from any MCP server.

The **Jupyter MCP server**, from the
[`jupyter-server-mcp`](https://github.com/jupyter-ai-contrib/jupyter-server-mcp)
package, runs inside the Jupyter server. Other packages add their tools to
it:

- [`jupyterlab-commands-toolkit`](https://github.com/jupyter-ai-contrib/jupyterlab-commands-toolkit)
  adds `list_all_commands` and `execute_command`, which run JupyterLab
  commands.
- The `jupyter-ai` package adds tools that read and edit notebooks, from
  [`jupyter-ai-tools`](https://github.com/jupyter-ai-contrib/jupyter-ai-tools).
- Your own packages can add tools too (see {doc}`/developers/agent-tools`).

Terminal agents connect to this server directly. Agents in the agent chat get
it automatically.

## JupyterLab commands

Everything you do in JupyterLab goes through a
[command](https://jupyterlab.readthedocs.io/en/latest/user/commands.html):
opening a file, running a cell, restarting a kernel, toggling a panel. Each
command has an ID, such as `notebook:run-all-cells`, and can take arguments.
Extensions add their own commands.

Commands are what makes an agent feel at home in JupyterLab: an agent that can
run commands can do almost anything you can do with the mouse and keyboard,
and see the result in your browser tab. Terminal agents and the agent chat
run commands through the Jupyter MCP server. Jupyternaut in the browser runs
them directly, since it lives in the same page.

This also means that an extension that adds a command adds a capability for
every agent.

## The Agent Client Protocol

The [Agent Client Protocol (ACP)](https://agentclientprotocol.com) is an open
standard for applications that host coding agents, in the same way that the
Language Server Protocol is for language tools. The agent chat uses ACP to
start agents, send them your messages, show their replies and tool calls, and
relay permission requests. Any agent that speaks ACP can work in the chat.

(concepts-live-updates)=
## Seeing changes live

An agent often edits files on disk while you have them open. By default,
JupyterLab keeps showing what it loaded and warns about the conflict when you
save. Two packages make open documents follow the file instead:

- **Real-time collaboration (RTC)**, from
  [Jupyter Collaboration](https://jupyterlab-realtime-collaboration.readthedocs.io),
  keeps a shared copy of each open document on the server. It updates open
  text files **and notebooks** when they change on disk, without losing
  outputs or the kernel.
- [`jupyter-live-content`](https://github.com/jupyter-ai-contrib/jupyter-live-content)
  reloads open text files, Markdown previews, and images, without RTC. It does
  not reload notebooks. The `jupyter-ai` package installs it.

When an agent changes a notebook through JupyterLab commands or through the
notebook tools of the `jupyter-ai` package, the change happens in the open
notebook, so you see it with or without these packages.

## Instructions and skills

Agents read project instructions from a file at the root of the project,
such as `AGENTS.md`. Use it to describe your project, and how you want the
agent to work with JupyterLab.

[Agent Skills](https://agentskills.io) are folders of instructions, scripts,
and references that an agent loads when a task needs them. Coding agents and
Jupyternaut in the browser both support them, so a skill written once can
teach every agent a workflow.

## Permissions

Agents can change files, run code, and run commands. Each setup lets you
decide what they may do without asking:

- Terminal agents ask for permission according to their own settings.
- The agent chat shows permission requests in the chat, with controls in the
  input toolbar.
- Jupyternaut in the browser has a list of commands that require your
  approval.

Whatever the setup, use version control, so that you can review and undo what
an agent did.
