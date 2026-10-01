# Terminal coding agents

Coding agents such as Claude Code, Codex CLI, GitHub Copilot CLI, Gemini CLI,
and OpenCode already read and write files, run commands, and fix their own
mistakes. Running one of them next to JupyterLab is often the most productive
way to work with AI in Jupyter: you keep the agent you already know, with its
own interface, model, and subscription, and JupyterLab becomes the place where
you see, run, and review the work.

With a few extensions installed, the agent can also act on JupyterLab itself.
It can open a file for you, run notebook cells in your kernel, read their
outputs, and show you the result, while edits it makes on disk appear live in
the documents you have open.

```{figure} https://raw.githubusercontent.com/jtpio/xtralab/main/images/hero.webp
:alt: JupyterLab with a file browser, a side-by-side diff, and Claude Code running in a terminal
:width: 100%
:class: screenshot

Claude Code in a JupyterLab terminal, next to a diff of its changes. This
screenshot shows xtralab, one of the {doc}`ready-made setups <examples>`.
```

## What you need

A productive setup has three parts:

1. **JupyterLab with a few extensions.** A Model Context Protocol (MCP) server
   that runs inside Jupyter, a toolkit that lets agents run JupyterLab
   commands, and live updates for open documents. One package, `ajlab`,
   installs all of them. See {doc}`setup`.
2. **The Jupyter MCP server registered with your agent.** You do this once
   per agent, with one command. See {doc}`connect`.
3. **The agent itself**, started from your project folder, in a JupyterLab
   terminal or anywhere else on the same machine.

```bash
pip install ajlab
jupyter lab
# then, in a terminal (for example File → New → Terminal in JupyterLab):
claude mcp add jupyter -- jupyter-server-mcp-proxy
claude
```

The example uses Claude Code. The {doc}`connect` page shows the commands for
other agents.

## How it works

```{mermaid}
flowchart LR
    agent["Coding agent<br/>terminal or desktop app"]
    subgraph server["Jupyter server"]
        mcp["Jupyter MCP server"]
        files[("Project files")]
    end
    lab["JupyterLab<br/>in your browser"]
    agent -- "MCP tools" --> mcp
    agent -- "reads and edits" --> files
    mcp -- "JupyterLab commands" --> lab
    files -- "live updates" --> lab
```

- The agent edits files on disk with its own tools, as it does in any project.
  JupyterLab picks up the changes and updates the open documents, including
  notebooks.
- When the agent needs JupyterLab itself, it calls tools on the Jupyter MCP
  server. The server forwards the call to your JupyterLab tab as a
  [JupyterLab command](https://jupyterlab.readthedocs.io/en/latest/user/commands.html),
  the same commands that menus, the command palette, and keyboard shortcuts
  use. The agent can open documents, run cells, and do almost anything else
  you can do in the interface.
- The agent connects through a small stdio proxy,
  `jupyter-server-mcp-proxy`, which finds the running Jupyter server by itself.
  You do not need to give a port or a token.

## Where the agent can run

| Where | Notes |
| --- | --- |
| A terminal in JupyterLab | The simplest option. The terminal uses the same environment as the server, so the proxy is already installed and the working directory is the server's root directory. Also works on remote servers and JupyterHub. |
| Your own terminal | Use the terminal app, tmux session, or editor you prefer. Start the agent in a folder that JupyterLab serves. |
| A desktop app | Apps that embed an agent, such as Claude Code in the Claude desktop app, can use the same MCP server when it is in their configuration. |

See {ref}`terminal-agents-where` for the details of each option.

## Compared with the agent chat

The {doc}`agent chat </users/chat/index>` runs agents from a chat panel inside
JupyterLab instead. Choose terminal agents when you:

- Already use a coding agent and want to keep its full interface, commands,
  and configuration.
- Want the newest agent features as soon as they ship.
- Work mostly with code and files, with notebooks as one part of the project.

Choose the agent chat when you want a chat panel in JupyterLab, shared chats
with other people, or a single interface for many different agents. The two
work together: the `jupyter-ai` package includes the Jupyter MCP server, so a
terminal agent can connect to it as well.

```{toctree}
:hidden:

setup
connect
workflows
examples
```
