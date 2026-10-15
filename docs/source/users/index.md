# User guide

Jupyter AI connects models, agents, and workflows to notebooks. Start from
what you want to accomplish, then choose the way of working that fits your
setup. All of them share the same building blocks, so you can combine them.

(user-guide-goals)=
## What do you want to accomplish?

| Goal | Where to start |
| --- | --- |
| **Debug a notebook** | Ask an agent to run the notebook, read the errors, and fix the code: a {ref}`terminal agent <terminal-agents-notebooks>`, the {ref}`agent chat <chat-notebook-tools>`, or {ref}`Jupyternaut in the browser <browser-features>`. In the agent chat, you can also {ref}`attach the failing cells <chat-attachments>` to your message. |
| **Edit and run notebooks with an agent** | {ref}`Terminal agents <terminal-agents-notebooks>` edit notebook files and run cells through JupyterLab. Agents in the {ref}`agent chat <chat-notebook-tools>` and {ref}`Jupyternaut in the browser <browser-features>` work in the open notebook. |
| **Create a domain workflow** | Write {ref}`instructions and skills <concepts-instructions-skills>` for your field, give agents {ref}`your own tools <chat-custom-mcp-servers>`, or build a {doc}`custom AI persona </developers/entry_points_api/index>`. |
| **Use a local or private model** | Point {ref}`Jupyternaut in the browser <browser-models>` or the {ref}`Jupyternaut persona <jupyternaut-ollama>` at Ollama, vLLM, or another OpenAI-compatible server. Agents such as OpenCode and Goose can also use local models through their own configuration. |
| **Connect an existing agent** | Register the Jupyter MCP server with {doc}`your terminal agent <terminal-agents/connect>`, or {ref}`install the agent <chat-install-agents>` for the agent chat. |
| **Add specialized tools** | Add {ref}`MCP servers <chat-custom-mcp-servers>` to the agent chat, or {doc}`write tools </developers/agent-tools>` that every agent can call. |

## Ways to use Jupyter AI

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
