# Contributors

This page is intended for people interested in building new or modified functionality for Jupyter AI.

## Code organization

Jupyter AI is distributed as a monorepo, including the core `jupyter_ai` package and a set of AI modules.

## Prerequisites

You can develop Jupyter AI on any system that can run a supported Python version, including recent Windows, macOS, and Linux versions. If you have not already done so, [download Python](https://www.python.org/downloads/) and install it. The commands below presume that you can run `python` and `pip` from your preferred terminal.

## Development install

First, install the Hatch CLI, which installs the Hatchling build backend automatically.

```
pip install hatch
```

Then, enter the default hatch environment, which automatically installs all dependencies and executes development setup when entering for the first time. This command must be run from the root of the monorepo (`<jupyter-ai-top>`).

```
cd <jupyter-ai-top>
hatch shell
```

Set up your development environment and start the server:

```
jlpm setup:dev # only needs to be run once
jlpm dev
```

Finally, in a separate shell, enter the hatch environment and build the project after making any changes.

```
cd <jupyter-ai-top>
hatch shell
jlpm build
```

To exit the hatch environment, on a blank command prompt, run `exit` or press `Ctrl+D`.

If installation fails for any reason, you will have to first uninstall the hatch environment and then test your fix by reinstalling.

## Development uninstall

To uninstall your Jupyter AI development environment, remove the Hatch environment:

```
hatch env remove default
```

