# Jupyter AI Module Cookiecutter

A [cookiecutter](https://github.com/audreyr/cookiecutter) template for creating
a AI module. The AI module constructed from the template serves as a very simple
example that can be extended however you wish. 
    
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

To register the new AI module as part of this monorepo, add the package to the
`options.python_packages` field in `.jupyter-releaser.toml`.
