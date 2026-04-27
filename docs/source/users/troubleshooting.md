# Troubleshooting

This page covers common issues you may encounter when using Jupyter AI and how to resolve them.

## Persona does not appear in chat

Make sure you have installed the corresponding agent and its dependencies, and
that you are using the latest version. See the
{doc}`Getting Started guide </getting-started>` for installation instructions.
Check the JupyterLab server logs for more information.

## Persona does not reply

You may not be authenticated with the agent's service. Try logging in through
the agent's CLI first, then restart JupyterLab. Some agents, like Goose or
OpenCode, will also require you to select an LLM before usage.

````{tabs}

```{tab} Claude

    claude login

```

```{tab} Codex

    codex

```

```{tab} GitHub Copilot

    copilot login

```

```{tab} Gemini

    gemini auth login

```

```{tab} Goose

    goose configure

```

```{tab} Kiro

    kiro-cli login

```

```{tab} Mistral Vibe

    vibe --setup

```

```{tab} OpenCode

    opencode auth login

```

````

For GitHub Copilot, you can also set `COPILOT_GITHUB_TOKEN`, `GH_TOKEN`, or
`GITHUB_TOKEN` before starting JupyterLab instead of running `copilot login`.
For Mistral Vibe, you can also set `MISTRAL_API_KEY` before starting JupyterLab
instead of running `vibe --setup`.

If the error persists after logging in, check the server logs and
[open an issue](https://github.com/jupyterlab/jupyter-ai/issues/new/choose) on
GitHub.

## Persona does not request permission before running tools

Some agents default to not requesting tool call permissions. We make a best
effort to enforce safer defaults, but this is challenging to configure across
all agents and is still under active development. Refer to your agent's
documentation for setting up tool call permissions and approval policies.

## Updates to agent configuration do not take effect

You will need to restart the JupyterLab server for configuration changes to take
effect in all chats:

```
# Stop the running server (Ctrl+C), then restart:
jupyter lab
```

## Chats take a long time to load (orange spinner)

Wait a few seconds and try closing other browser tabs with JupyterLab open to
see if that helps. This is a known issue and we are working to address it.
