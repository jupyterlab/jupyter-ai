# Contributors

This page is intended for people interested in building new or modified functionality for Jupyter AI.

## Prerequisites

You can develop Jupyter AI on any system that can run a supported Python version up to and including 3.11, including recent Windows, macOS, and Linux versions.

Each Jupyter AI major version works with only one major version of JupyterLab. Jupyter AI 1.x supports JupyterLab 3.x, and Jupyter AI 2.x supports JupyterLab 4.x.

We highly recommend that you install [conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html) to start developing on Jupyter AI, especially if you are developing on macOS on an Apple Silicon-based Mac (M1, M1 Pro, M2, etc.).

You will need Node.js 18 to use Jupyter AI. Node.js 18.16.0 is known to work.

:::{warning}
:name: node-18-15
Due to a compatibility issue with Webpack, Node.js 18.15.0 does not work with Jupyter AI.
:::

## Development install
After you have installed the prerequisites, create a new conda environment and activate it.

```
conda create -n jupyter-ai python=3.11
conda activate jupyter-ai
```

This command must be run from the root of the monorepo (`<jupyter-ai-top>`).

```
# Move to the root of the repo package
cd <jupyter-ai-top>

# Installs all the dependencies and sets up the dev environment
./scripts/install.sh
```

Start and launch JupyterLab in your default browser:

```
jlpm dev
```

You can open a new terminal and use that to build and push changes to the repository. Enter the `conda` environment and build the project after making any changes.

```
cd <jupyter-ai-top>
conda activate jupyter-ai
jlpm build
```

To change what Jupyter AI packages are installed in your dev environment, use the `dev-uninstall` script:

```
# uninstalls all Jupyter AI packages
jlpm dev-uninstall
```

To reinstall Jupyter AI packages back into your dev environment, use the `dev-install` script:

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

## Building documentation

The `./scripts/install.sh` should automatically install the documentation
dependencies. To build the documentation locally, run

```
cd docs/
make html
```

and open `file://<JUPYTER-AI-ABSOLUTE-PATH>/docs/build/html/index.html`, where
`<JUPYTER-AI-ABSOLUTE-PATH>` is the absolute path of the Jupyter AI monorepo on
your local filesystem. It is helpful to bookmark this path in your browser of
choice to easily view your local documentation build.

After making any changes, make sure to rebuild the documentation locally via
`make html`, and then refresh your browser to verify the changes visually.


## Development uninstall

To uninstall your Jupyter AI development environment, deactivate and remove the Conda environment:

```
conda deactivate
conda env remove -n jupyter-ai
```
