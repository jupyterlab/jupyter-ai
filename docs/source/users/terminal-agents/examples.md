# Ready-made setups

You can assemble a setup for terminal agents from the packages in
{doc}`setup`, or start from one of these.

## jupyter-ai-core: the minimal setup

`jupyter-ai-core` is a meta-package. It installs JupyterLab,
`jupyter-server-mcp`, `jupyterlab-commands-toolkit`, and
`jupyter-live-content`, and it shows hidden files by default. It adds nothing
else: what you get is the standard JupyterLab, ready for an agent.

```bash
pip install jupyter-ai-core
```

Use it as a starting point, or as a dependency of your own distribution.

## The Jupyter AI package

The `jupyter-ai` package provides the {doc}`agent chat </users/chat/index>`.
It also runs the Jupyter MCP server with the commands toolkit and a set of
notebook tools, so a terminal agent can connect to it as described in
{doc}`connect`. Use it when you want both: a chat panel in JupyterLab,
and your coding agent in a terminal.

(terminal-agents-own-distribution)=
## Make your own distribution

A team or a course often wants the same setup for everyone. Like
`jupyter-ai-core`, you can publish a small Python package that depends on the
extensions and ships default settings. It can build on `jupyter-ai-core`, and
add what your team needs, such as real-time collaboration for live notebook
updates and the Git extension.

The dependencies go in `pyproject.toml`, and the default settings are data
files that the package installs in the environment's Jupyter configuration
directories. With [Hatch](https://hatch.pypa.io):

```toml
[project]
name = "my-lab"
dependencies = [
  "jupyter-ai-core",
  "jupyter-server-ydoc",
  "jupyter-docprovider",
  "jupyterlab-git",
]

[tool.hatch.build.targets.wheel.shared-data]
"jupyter-config/jupyter_server_config.d" = "etc/jupyter/jupyter_server_config.d"
"jupyter-config/labconfig" = "etc/jupyter/labconfig"
```

With this layout:

- `jupyter-config/jupyter_server_config.d/my-lab.json` holds server settings,
  such as `{"ContentsManager": {"allow_hidden": true}}`.
- `jupyter-config/labconfig/default_setting_overrides.d/00-my-lab.json` holds
  default JupyterLab settings, keyed by plugin ID, such as
  `{"@jupyterlab/filebrowser-extension:browser": {"showHiddenFiles": true}}`.

Users can still change these settings: their own settings take precedence
over the defaults.
