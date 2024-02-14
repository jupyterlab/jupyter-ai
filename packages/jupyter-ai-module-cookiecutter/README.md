# Jupyter AI module cookiecutter

A [cookiecutter](https://github.com/cookiecutter/cookiecutter) template for creating
a Jupyter AI module. A Jupyter AI module is a Python package that registers
additional model providers (containing language and embedding models) and slash
commands for Jupyter AI.

This cookiecutter generates a simple AI module that provides a test model
provider and slash command implementation that can be used in Jupyter AI once
installed. Developers should use this as a template to implement additional
functionality on top of Jupyter AI.

## Usage

Install cookiecutter.

```
pip install cookiecutter
```

Then from the project root, run these commands:

```
cd packages/
cookiecutter jupyter-ai-module-cookiecutter
```

Follow the prompts to create a new AI module under `packages/`.

To install the new AI module locally:

```
cd "<jai-module-root-dir>"
pip install -e "."
```

See the `README.md` under the root directory for more information.
