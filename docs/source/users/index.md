# User guide

There is more than one way to work with AI agents in Jupyter. They differ in
where the agent runs and how you talk to it, and they share the same building
blocks, so you can combine them.

::::{grid} 1 1 3 3
:gutter: 2

:::{grid-item-card} 🖥️ Terminal coding agents
:link: terminal-agents/index
:link-type: doc

Run Claude Code, Codex, or another coding agent in a terminal, and connect it
to JupyterLab with MCP.
:::

:::{grid-item-card} 💬 Agent chat
:link: chat/index
:link-type: doc

Chat with agents in a JupyterLab side panel, with permission prompts and
shared chats.
:::

:::{grid-item-card} 🌐 In the browser
:link: browser/index
:link-type: doc

An assistant that runs in the browser tab with your own API key, also in
JupyterLite.
:::

::::

## Compare the options

| | Terminal coding agents | Agent chat | In the browser |
| --- | --- | --- | --- |
| **You talk to the agent in** | The agent's own interface: a terminal, a desktop app, or an editor | A chat panel in JupyterLab | A chat panel in JupyterLab, Jupyter Notebook, or JupyterLite |
| **The agent runs** | In its own process, started by you | In a process started by the Jupyter server | In the browser tab |
| **Agents** | Any agent that supports MCP | Agents that support ACP: Claude, Codex, GitHub Copilot, Gemini, Goose, Kiro, Mistral Vibe, OpenCode, and more | Jupyternaut, with models from Anthropic, Google, Mistral, OpenAI, OpenRouter, or any OpenAI-compatible server |
| **Model access** | The agent's own sign-in or API key | The agent's own sign-in or API key | An API key, or a local model server |
| **Acts on JupyterLab through** | The Jupyter MCP server | The Jupyter MCP server | JupyterLab commands, directly |
| **Needs a Jupyter server** | Yes | Yes | No: also runs in JupyterLite |
| **Install** | `pip install ajlab` | `pip install jupyter-ai` | `pip install jupyterlite-ai` |

## Which one should I use?

- **You already use a coding agent** such as Claude Code or Codex: start with
  {doc}`terminal-agents/index`. You keep your agent as it is, and it learns to
  work with JupyterLab.
- **You want a chat panel inside JupyterLab**, to try several agents or to
  share chats with other people: use the {doc}`agent chat <chat/index>`.
- **You cannot install agents on the server**, deploy JupyterLite, or want
  the smallest setup with an API key: use {doc}`Jupyternaut in the browser
  <browser/index>`.
- **You want to prompt a model from a notebook cell**: use the
  {doc}`magic commands <magic_commands/index>`.

The options are not exclusive. The `jupyter-ai` package runs the same
Jupyter MCP server that terminal agents use, so you can keep a coding agent in
a terminal next to the chat panel. See {doc}`concepts` for the building
blocks they share.

## More projects

Many more AI extensions for Jupyter exist, from other teams and companies.
{doc}`ecosystem` points to a community-maintained list.

```{toctree}
:hidden:

concepts
terminal-agents/index
chat/index
browser/index
magic_commands/index
ecosystem
troubleshooting
versioning
```
