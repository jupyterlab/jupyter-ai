---
layout: landing
description: Jupyter AI is the open, Jupyter-native integration layer that connects models, agents, and workflows to computational notebooks.
---

```{raw} html
:file: _templates/hero-icon.html
```

# Jupyter AI

```{rst-class} lead
Jupyter AI is the open, Jupyter-native integration layer that connects models, agents, and workflows to computational notebooks.
```

```{container} buttons
[Get Started](getting-started)
[{octicon}`mark-github;1.2em` GitHub](https://github.com/jupyterlab/jupyter-ai)
```

---

## What do you want to accomplish?

::::{grid} 1 1 2 3
:gutter: 2
:padding: 0
:class-row: surface

:::{grid-item-card} 🐞 Debug a Notebook
Ask an agent to run your notebook, read the errors and outputs, and fix the code. Or attach the failing cells to a chat.
+++
{ref}`Terminal agent <terminal-agents-notebooks>` · {ref}`Agent chat <chat-attachments>` · {ref}`In the browser <browser-features>`
:::

:::{grid-item-card} 📝 Edit and Run Notebooks
Let an agent write cells and run them in your kernel, while you watch the notebook update.
+++
{ref}`Terminal agent <terminal-agents-notebooks>` · {ref}`Agent chat <chat-notebook-tools>` · {ref}`In the browser <browser-features>`
:::

:::{grid-item-card} 🧪 Create a Domain Workflow
Package the instructions, skills, and tools of your field, so that agents follow the way your team works.
+++
{ref}`Instructions and skills <concepts-instructions-skills>` · {doc}`Custom personas <developers/entry_points_api/index>`
:::

:::{grid-item-card} 🔒 Use a Local or Private Model
Run models on your own infrastructure with Ollama, vLLM, or any OpenAI-compatible server.
+++
{ref}`In the browser <browser-models>` · {ref}`Jupyternaut persona <jupyternaut-ollama>`
:::

:::{grid-item-card} 🤖 Connect an Existing Agent
Bring Claude Code, Codex, GitHub Copilot, or another agent you already use, in a terminal or in the JupyterLab chat.
+++
{doc}`Terminal agent <users/terminal-agents/connect>` · {ref}`Agent chat <chat-install-agents>`
:::

:::{grid-item-card} 🧰 Add Specialized Tools
Give agents your own tools and data sources, with MCP servers, Python functions, or JupyterLab commands.
+++
{ref}`MCP servers <chat-custom-mcp-servers>` · {doc}`Build tools <developers/agent-tools>`
:::

::::

## Ways to Use Jupyter AI

All of them build on the same foundation, and you can combine them.

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
