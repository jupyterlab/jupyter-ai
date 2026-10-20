# Jupyternaut in the browser

Jupyternaut is an AI assistant that runs entirely in your browser tab. It
answers in Jupyter chats, suggests code completions as you type, and works
with your notebooks through JupyterLab commands: it can create notebooks, add
and edit cells, run them, and read their outputs. It comes from
[Jupyter AI Lite](https://github.com/jupyterlab/jupyter-ai-lite).

Jupyternaut calls the model provider directly from the browser, with your own
API key, or a model server running on your machine. There is no agent to
install on the server, which makes it work where other setups cannot: in
[JupyterLite](https://jupyterlite.readthedocs.io), which has no server at all,
and on shared deployments where you cannot install agent programs.

The chat works like the {doc}`agent chat </users/chat/index>`: chats are
`.chat` files, and you pick Jupyternaut and its model in the input toolbar of
the chat.

:::{tip}
Try it now, without installing anything, in the
[online demo](https://jupyterlab.github.io/jupyter-ai-lite/lab/index.html). The demo runs
in JupyterLite: you only need an API key from a model provider.
:::

## When to use it

- You deploy **JupyterLite**, for example for teaching or for documentation
  examples.
- You want the **smallest setup**: one package and an API key, with no agent
  to install or sign in to.
- You use **Jupyter Notebook** as well as JupyterLab.
- You run models **locally**, with Ollama or another OpenAI-compatible server.

If you already use a coding agent such as Claude Code or Codex, or want an
agent that runs shell commands, see {doc}`/users/terminal-agents/index` or
the {doc}`agent chat </users/chat/index>` instead.

## Install

Jupyternaut in the browser is installed with the `jupyter-ai-lite` package.
It works in JupyterLab and Jupyter Notebook as well as in JupyterLite.

````{tabs}

```{tab} JupyterLab and Notebook

    pip install jupyter-ai-lite

```

```{tab} JupyterLite

    # in the environment where you build the site
    pip install jupyterlite-core jupyter-ai-lite
    jupyter lite build

```

````

It needs JupyterLab 4.5 or Jupyter Notebook 7.5, or later.

(browser-models)=
## Choose a model

1. Open **Settings → Jupyternaut Settings**, or run **Jupyternaut Settings**
   from the command palette.
2. In the **Providers** section, click **Add a new provider**.
3. Choose a provider, a model, and enter your API key.
4. Create a chat, for example from the **Chat** card of the JupyterLab
   launcher, and select Jupyternaut and the model in the input toolbar of the
   chat.

| Provider | Notes |
| --- | --- |
| Anthropic, Google, Mistral, OpenAI | Use an API key from the provider. |
| [OpenRouter](https://openrouter.ai) | Models from many providers with a single account. You can connect your account from the dialog instead of entering a key. |
| Generic (OpenAI-compatible) | Any server with an OpenAI-compatible API, such as [Ollama](https://ollama.com) or a LiteLLM proxy, with its base URL. |

:::{important}
By default, API keys are kept in memory only, and you need to enter them
again after reloading the page. You can choose to store them in the settings
instead, but they are then saved as plain text: on the server with JupyterLab,
or in the browser with JupyterLite.
:::

(browser-features)=
## What it can do

- **Chat** in `.chat` files, with files and notebook cells as attachments.
  The input toolbar of the chat shows the token and context usage.
- **Code completions** in notebooks and editors, with the same or a different
  model.
- **Work with notebooks and files** through JupyterLab commands. You choose
  which commands need your approval before they run.
- **Agent Skills**: Jupyternaut loads skills from the `.agents/skills/` and
  `_agents/skills/` folders of your workspace, in the
  [Agent Skills](https://agentskills.io) format that coding agents use.
- **Remote MCP servers**, when they support the Streamable HTTP transport and
  allow requests from the browser (CORS). Most MCP servers run as local
  programs and cannot be used from a browser.
- **Web search and fetch**, with provider-hosted tools or a fetch from the
  browser.

## Learn more

The [full documentation](https://jupyter-ai-lite.readthedocs.io) covers each
provider, MCP servers, skills, web retrieval, and how to add your own
providers.
