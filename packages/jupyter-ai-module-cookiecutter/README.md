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

# Usage (monorepo integration)

To integrate the new AI module into this monorepo, execute this command
manually from the AI module root:

```
rm -r .github/ binder/ CHANGELOG.md RELEASE.md
```

Then, add the package to the `options.python_packages` field in
`.jupyter-releaser.toml`.
