# jupyter-ai

[![Github Actions Status](https://github.com/jupyterlab/jupyter_ai/workflows/Build/badge.svg)](https://github.com/jupyterlab/jupyter_ai/actions/workflows/build.yml)

A generative AI extension for Jupyter, to allow for AI to interact with notebooks and other documents. Documentation is available on [ReadTheDocs](https://jupyter-ai.readthedocs.io/en/latest/).

This is a monorepo that houses the core `jupyter_ai` package in addition to the
default supported AI modules. To learn more about the core package, please refer
to the [README](packages/jupyter-ai/README.md).

### Development install

Install the Hatch CLI, which installs the Hatchling build backend automatically.

```
pip install hatch
```

Then, simply enter the default hatch environment, which automatically installs
all dependencies and executes development setup when entering for the first
time. This command must be run with the current directory set to the root of the
monorepo (`<jupyter-ai-top>`).

```
cd <jupyter-ai-top>
hatch shell
```

Set up your development environment and start the server:

```
jlpm setup:dev # only needs to be run once
jlpm dev
```

Finally, in a separate shell, enter the hatch environment and build the project
after making any changes.

```
cd <jupyter-ai-top>
hatch shell
jlpm build
```

To exit the hatch environment at any time, exit like you would normally exit a
shell process, via the `exit` command or `Ctrl+D`.

If installation fails for any reason, you will have to first uninstall the hatch
environment and then test your fix by reinstalling. See "Uninstall" procedure
below.

### Uninstall

Just remove the hatch environment:

```
hatch env remove default
```
