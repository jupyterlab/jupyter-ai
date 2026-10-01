---
layout: landing
description: Jupyter AI brings AI agents to Jupyter. Connect the coding agent you already use, chat with agents in JupyterLab, or run an assistant in the browser.
---

```{raw} html
:file: _templates/hero-icon.html
```

# Jupyter AI

```{rst-class} lead
AI agents for Jupyter, built on open standards. Connect the coding agent you already use, chat with agents in JupyterLab, or run an assistant in the browser.
```

```{container} buttons
[Get Started](getting-started)
[{octicon}`mark-github;1.2em` GitHub](https://github.com/jupyterlab/jupyter-ai)
```

---

## Choose how you work

::::{grid} 1 1 3 3
:gutter: 2
:padding: 0
:class-row: surface

:::{grid-item-card} 🖥️ Terminal Coding Agents
:link: users/terminal-agents/index
:link-type: doc

Keep Claude Code, Codex, or your favorite agent in a terminal. Connect it to JupyterLab so it can open files, run cells, and drive the interface.
:::

:::{grid-item-card} 💬 Agent Chat
:link: users/chat/index
:link-type: doc

Chat with Claude, Codex, GitHub Copilot, Gemini, and other agents in a JupyterLab side panel, and share chats with your team.
:::

:::{grid-item-card} 🌐 In the Browser
:link: users/browser/index
:link-type: doc

Jupyternaut runs in your browser tab with your own API key. Works in JupyterLab, Jupyter Notebook, and JupyterLite.
:::

::::

## Features

::::{grid} 1 1 2 3
:gutter: 2
:padding: 0
:class-row: surface

:::{grid-item-card} 🔌 Open Standards
Agents connect through MCP and ACP. Use the agents and models you already have, with no lock-in.
:::

:::{grid-item-card} ⚡ Live Notebooks
Watch agents open files, run notebooks, and fix cell errors in real time.
:::

:::{grid-item-card} 🛡️ Guardrails
Approve file writes, commands, and tool calls before agents run them.
:::

:::{grid-item-card} 🤝 Collaborative Chats
Collaborate with AI personas and other people in shared chats, with files and cells as attachments.
:::

:::{grid-item-card} 📓 Notebook Magics
Prompt a model from a notebook cell with the `%%ai` magic command.
:::

:::{grid-item-card} 🧩 Flexible and Extensible
Add a JupyterLab command or a Python function, and every agent can use it. Build your own AI personas.
:::

::::


```{toctree}
:hidden:

getting-started
users/index
contributors/index
developers/index
roadmap/index
releases/index
```
