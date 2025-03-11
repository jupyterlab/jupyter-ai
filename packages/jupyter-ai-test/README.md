# jupyter_ai_test

`jupyter_ai_test` is a Jupyter AI module that registers additional model
providers and slash commands for testing Jupyter AI in a local development
environment. This package should never published on NPM or PyPI.

## Requirements

- Python 3.9 - 3.12
- JupyterLab 4

## Install

To install the extension, execute:

```bash
pip install jupyter_ai_test
```

## Uninstall

To remove the extension, execute:

```bash
pip uninstall jupyter_ai_test
```

## Contributing

### Development install

```bash
cd jupyter-ai-test
pip install -e "."
```

### Development uninstall

```bash
pip uninstall jupyter_ai_test
```

#### Backend tests

This package uses [Pytest](https://docs.pytest.org/) for Python testing.

Install test dependencies (needed only once):

```sh
cd jupyter-ai-test
pip install -e ".[test]"
```

To execute them, run:

```sh
pytest -vv -r ap --cov jupyter_ai_test
```
