# Ready-made setups

You can assemble a setup for terminal agents from the packages in
{doc}`setup`, or start from one of these distributions. They show different
points on the same line: from the minimum that works, to an environment
reshaped around coding agents.

## ajlab: the minimal setup

[`ajlab`](https://github.com/jtpio/ajlab) ("agent-ready JupyterLab") is a
meta-package. It installs JupyterLab, `jupyter-server-mcp`,
`jupyterlab-commands-toolkit`, and the RTC packages for live updates, and it
shows hidden files by default. It adds nothing else: what you get is the
standard JupyterLab, ready for an agent.

```bash
pip install ajlab
```

Use it as a starting point, or as a dependency of your own distribution.

## xtralab: an environment built around agents

[xtralab](https://github.com/jtpio/xtralab) builds on `ajlab` and shows how far
the integration between JupyterLab and terminal agents can go. You do not need
it to use a terminal agent with JupyterLab, but it is a good source of ideas.
It adds:

- **An agent launcher**, with one button for each coding agent installed on
  the machine, an optional first prompt, and the list of files the agent
  changed.
- **Side-by-side git diffs** for text files and notebooks, editable in place.
- **Ask an agent**: select code, type an instruction, and send it with the
  file path and line numbers to a new or running agent.
- **A terminals panel** that shows the agent running in each terminal and its
  latest output.
- **Agent Skills** for JupyterLab: `customize-jupyterlab` teaches an agent
  where each JupyterLab setting lives, and `guided-code-walkthrough` lets it
  give you a tour of the code in the running app, through the Jupyter MCP
  server.
- **A desktop app** for macOS and Linux, with its own Python runtime.

```bash
pip install xtralab
```

See the [xtralab documentation](https://jtpio.github.io/xtralab/) for the
details.

## The Jupyter AI package

The `jupyter-ai` package provides the {doc}`agent chat </users/chat/index>`.
It also runs the Jupyter MCP server with the commands toolkit and a set of
notebook tools, so a terminal agent can connect to it with the same
registration as above. Use it when you want both: a chat panel in JupyterLab,
and your coding agent in a terminal.

(terminal-agents-own-distribution)=
## Make your own distribution

A team or a course often wants the same setup for everyone. Like `ajlab`, you
can publish a small Python package that depends on the extensions and ships
default settings.

The dependencies go in `pyproject.toml`, and the default settings are data
files that the package installs in the environment's Jupyter configuration
directories. With [Hatch](https://hatch.pypa.io):

```toml
[project]
name = "my-lab"
dependencies = [
  "jupyterlab>=4.6",
  "jupyter-server-mcp",
  "jupyterlab-commands-toolkit",
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
