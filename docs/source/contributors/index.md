# Contributors

This page is intended for people interested in building new or modified functionality for Jupyter AI.

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

To change what Jupyter AI packages are installed in your Hatch environment, use the `dev-uninstall` script:

```
# uninstalls all Jupyter AI packages
jlpm dev-uninstall
```

To reinstall Jupyter AI packages back into your Hatch environment, use the `dev-install` script:

```
# installs all Jupyter AI packages
jlpm dev-install
```

To only install/uninstall a subset of Jupyter AI packages, use the `--scope` argument that gets forwarded to Lerna:

```
# installs jupyter_ai_magics and its dependencies
jlpm dev-install --scope "@jupyter-ai/magics"
```

## Making changes while your server is running

If you change, add, or remove a **magic command**, after rebuilding, restart the kernel
or restart the server.

If you make changes to the **user interface** or **lab extension**, run `jlpm build` and then
refresh your browser tab.

## Development uninstall

To uninstall your Jupyter AI development environment, remove the Hatch environment:

```
hatch env remove default
```
