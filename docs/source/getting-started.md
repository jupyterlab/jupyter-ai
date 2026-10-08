# Get started

Jupyter AI offers several ways to work with AI agents in Jupyter. Pick the
one that matches how you work. Each one takes a few minutes to set up, and
the {doc}`user guide </users/index>` compares them in detail.

## Use your coding agent with JupyterLab

For people who already use Claude Code, Codex, GitHub Copilot CLI, Gemini CLI,
OpenCode, or another coding agent. The agent runs in a terminal, and connects
to JupyterLab to open files, run notebook cells, and drive the interface.

1. Install JupyterLab with the extensions for agents, and start it in your
   project folder:

   ```bash
   pip install ajlab
   jupyter lab
   ```

2. Open a terminal in JupyterLab (**File → New → Terminal**), and register the
   Jupyter MCP server with your agent:

   ::::{tab-set}

   :::{tab-item} Claude Code
   :sync: claude

   ```bash
   claude mcp add --scope user jupyter -- jupyter-server-mcp-proxy
   ```
   :::

   :::{tab-item} Codex
   :sync: codex

   ```bash
   codex mcp add jupyter -- jupyter-server-mcp-proxy
   ```
   :::

   :::{tab-item} Other agents
   :sync: other

   Add a stdio MCP server named `jupyter`, with the command
   `jupyter-server-mcp-proxy`. See {doc}`/users/terminal-agents/connect`.
   :::

   ::::

3. Start the agent in the same terminal, and ask it to work in JupyterLab:

   > Create a notebook that loads `data.csv` and plots it, then run all its cells.

Continue with {doc}`/users/terminal-agents/index`.

## Chat with agents in JupyterLab

For people who want a chat panel in JupyterLab, where they can use several
agents, approve their actions, and share chats with others.

1. Install Jupyter AI:

   ```bash
   pip install jupyter-ai
   ```

2. Install at least one agent, such as
   [Claude Code](https://docs.anthropic.com/en/docs/claude-code/quickstart) or
   [Codex CLI](https://developers.openai.com/codex/cli), and its ACP adapter if
   it needs one. The {doc}`agent chat guide </users/chat/index>` lists them.

3. Start JupyterLab, and open a chat from the **Chat** card in the launcher:

   ```bash
   jupyter lab
   ```

Continue with {doc}`/users/chat/index`.

## Run an assistant in the browser

For JupyterLite deployments, Jupyter Notebook users, and anyone who wants a
setup with only an API key. Jupyternaut runs in the browser tab and calls the
model provider directly.

1. Install the extension:

   ```bash
   pip install jupyterlite-ai
   ```

2. Start JupyterLab or Jupyter Notebook, open **Jupyternaut Settings** from the
   command palette, and add a model provider with your API key.

3. Open the chat panel and start a conversation.

You can also try it in the [online demo](https://jupyterlite.github.io/ai/lab/index.html).
Continue with {doc}`/users/browser/index`.

## Prompt a model from a notebook cell

For people who want to call a model from code cells with `%%ai`.

```bash
pip install jupyter-ai-magic-commands
```

Then, in a notebook:

```python
%load_ext jupyter_ai_magic_commands
```

Continue with {doc}`/users/magic_commands/index`.
