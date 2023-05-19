# jupyter_ai

[![Github Actions Status](https://github.com/jupyterlab/jupyter_ai/workflows/Build/badge.svg)](https://github.com/jupyterlab/jupyter_ai/actions/workflows/build.yml)
A generative AI extension for JupyterLab

This extension is composed of a Python package named `jupyter_ai`
for the server extension and a NPM package named `jupyter_ai`
for the frontend extension.

## Requirements

- JupyterLab >= 3.5 (not JupyterLab 4)
- Jupyter Server >= 2.0.0

## Installation

You can use `conda` or `pip` to install Jupyter AI. If you're using macOS on an Apple Silicon-based Mac (M1, M1 Pro, M2, etc.), we strongly recommend using `conda`.

Because of Ray's incompatibility with Python 3.11, you must use Python 3.9, or 3.10 with Jupyter AI. The instructions below presume that you are using Python 3.10.

Before you can use Jupyter AI, you will need to install any packages and set environment variables with API keys for the model providers that you will use. See [our documentation](https://jupyter-ai.readthedocs.io/en/latest/users/index.html) for details about what you'll need.

### With pip

    $ pip install jupyter_ai

### With conda

First, install [conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html) and create an environment that uses Python 3.10:

    $ conda create -n jupyter-ai python=3.10 conda pip
    $ conda activate jupyter-ai
    $ pip install jupyter_ai

If you are using an Apple Silicon-based Mac (M1, M1 Pro, M2, etc.), you need to uninstall the `pip` provided version of `grpcio` and install the version provided by `conda` instead.

    $ pip uninstall grpcio; conda install grpcio 

## Uninstall

To remove the extension, execute:

    $ pip uninstall jupyter_ai

## Usage with GPT-3

To use the `GPT3ModelEngine` in `jupyter_ai`, you will need an OpenAI API key.
Copy the API key and then create a Jupyter config file locally at `config.py` to
store the API key.

```python
c.GPT3ModelEngine.api_key = "<your-api-key>"
```

Finally, start a new JupyterLab instance pointing to this configuration file.

```bash
jupyter lab --config=config.py
```

If you are doing this in a Git repository, you can ensure you never commit this
file on accident by adding it to `.git/info/exclude`.

Alternately, you can also specify your API key while launching JupyterLab.

```bash
jupyter lab --GPT3ModelEngine.api_key=<api-key>
```

## Troubleshoot

If you can see the extension UI, but it is not working, check
that the server extension is enabled:

```bash
jupyter server extension list
```

If the server extension is installed and enabled, but you don't see
the extension UI, verify that the frontend extension is installed:

```bash
jupyter labextension list
```

## Contributing

### Development install

Note: You will need NodeJS to build the extension package.

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Change directory to the jupyter_ai directory
# Install package in development mode
pip install -e .
# Link your development version of the extension with JupyterLab
jupyter labextension develop . --overwrite
# Server extension must be manually installed in develop mode
jupyter server extension enable jupyter_ai
# Rebuild extension Typescript source after making changes
jlpm build
```

You can watch the source directory and run JupyterLab at the same time in different terminals to watch for changes in the extension's source and automatically rebuild the extension.

```bash
# Watch the source directory in one terminal, automatically rebuilding when needed
jlpm watch
# Run JupyterLab in another terminal
jupyter lab
```

With the watch command running, every saved change will immediately be built locally and available in your running JupyterLab. Refresh JupyterLab to load the change in your browser (you may need to wait several seconds for the extension to be rebuilt).

By default, the `jlpm build` command generates the source maps for this extension to make it easier to debug using the browser dev tools. To also generate source maps for the JupyterLab core extensions, you can run the following command:

```bash
jupyter lab build --minimize=False
```

### Development uninstall

```bash
# Server extension must be manually disabled in develop mode
jupyter server extension disable jupyter_ai
pip uninstall jupyter_ai
```

In development mode, you will also need to remove the symlink created by `jupyter labextension develop`
command. To find its location, you can run `jupyter labextension list` to figure out where the `labextensions`
folder is located. Then you can remove the symlink named `jupyter_ai` within that folder.

### Testing the extension

#### Server tests

This extension is using [Pytest](https://docs.pytest.org/) for Python code testing.

Install test dependencies (needed only once):

```sh
pip install -e ".[test]"
```

To execute them, run:

```sh
pytest -vv -r ap --cov jupyter_ai
```

#### Frontend tests

This extension is using [Jest](https://jestjs.io/) for JavaScript code testing.

To execute them, execute:

```sh
jlpm
jlpm test
```

#### Integration tests

This extension uses [Playwright](https://playwright.dev/docs/intro/) for the integration tests (aka user level tests).
More precisely, the JupyterLab helper [Galata](https://github.com/jupyterlab/jupyterlab/tree/master/galata) is used to handle testing the extension in JupyterLab.

More information are provided within the [ui-tests](./ui-tests/README.md) README.

### Packaging the extension

See [RELEASE](RELEASE.md)
