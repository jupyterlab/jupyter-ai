# {{ cookiecutter.python_name }}

This package is a Jupyter AI module named `{{ cookiecutter.python_name }}`
that registers a model provider for the Jupyter AI server extension.

## Requirements

- Python 3.8 - 3.11
- JupyterLab 4

## Install

To install the extension, execute:

```bash
pip install {{ cookiecutter.python_name }}
```

## Uninstall

To remove the extension, execute:

```bash
pip uninstall {{ cookiecutter.python_name }}
```

## Contributing

### Development install

```bash
cd {{ cookiecutter.root_dir_name }}
pip install -e "."
```

### Development uninstall

```bash
pip uninstall {{ cookiecutter.python_name }}
```

#### Backend tests

This package uses [Pytest](https://docs.pytest.org/) for Python testing.

Install test dependencies (needed only once):

```sh
cd {{ cookiecutter.root_dir_name }}
pip install -e ".[test]"
```

To execute them, run:

```sh
pytest -vv -r ap --cov {{ cookiecutter.python_name }}
```
