# Contributors

This page is intended for people interested in building new or modified functionality for Jupyter AI.

## Prerequisites

You can develop Jupyter AI on any system that can run a supported Python version up to and including 3.10, including recent Windows, macOS, and Linux versions. Python 3.11 is **not supported** due
to incompatibility with the [ray](https://pypi.org/project/ray/) library that we use.
If you are using an Apple Silicon-based Mac (M1, M1 Pro, M2, etc.), you need to install [Conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html) and follow the additional instructions to install the `grpcio` library from conda.

To use the `jupyter_ai` package in JupyterLab, as the development environment below does, you will need a currently-maintained version of JupyterLab 3. We do not yet support JupyterLab 4. If you use `conda`, you can install JupyterLab in your environment by running:

```
conda install jupyterlab
```

You will need Node.js 18 to use Jupyter AI. Node.js 18.16.0 is known to work.

:::{warning}
:name: node-18-15
Due to a compatibility issue with Webpack, Node.js 18.15.0 does not work with Jupyter AI.
:::

## Development install
This command must be run from the root of the monorepo (`<jupyter-ai-top>`).

```
cd <jupyter-ai-top>
./scripts/install.sh
```

Set up your development environment and start the server:

```
jlpm dev
```

Finally, in a separate shell, enter the `conda` environment and build the project after making any changes.

```
cd <jupyter-ai-top>
conda <your-conda-env>
jlpm build
```

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

To uninstall your Jupyter AI development environment, deactivate and remove the Conda environment:

```
conda deactivate
conda env remove -n <your-conda-env>
```
