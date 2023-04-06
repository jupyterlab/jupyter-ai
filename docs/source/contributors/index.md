# Contributors

This page is intended for people interested in building new or modified functionality for Jupyter AI.

## AI module and task definitions

Jupyter AI is distributed as a monorepo, including the core `jupyter_ai` package and a set of AI modules.

An **AI module** provides an interface between a Jupyter notebook and a generative artificial intelligence (GAI) algorithm. It defines one or more **tasks**. A task has the following properties, as specified in `tasks.py`:

* **ID** (`id`) — A unique text identifier for the task.
* **Task name** (`name`) — A friendly name that appears in the Jupyter notebook user interface. It should be styled as a menu item would, with a verb and without definite articles.
  * Good task names: "Generate image below", "Explain code"
  * Bad task names: "Image generation" (no verb), "Explain the code" (definite article)
* **Prompt template** (`prompt_template`) — The prompt to be sent to the GAI algorithm, with the special string `{body}` to be replaced with the contents of the current cell or the highlighted portion of the cell.
* **Modality** (`modality`) — The type of information that the task takes as input and emits as output. Supported modalities include:
  * `txt2txt` — Text input, text output (as code, markdown, or both)
  * `txt2img` — Text input, image output
* **Insertion mode** (`insertion_mode`) — The way the task's output will be added to the notebook or document. Supported insertion modes include:
  * `above` — AI output will be inserted above the selected text
  * `replace` — AI output will replace the selected text
  * `below` — AI output will be inserted below the selected text
  * `above-in-cells` — AI output will be inserted above the current cell, in new notebook cells
  * `below-in-cells` — AI output will be inserted below the current cell, in new notebook cells
  * `below-in-image` — AI output will be inserted below the current cell, as an image

AI modules can register new tasks, modalities, and insertion modes.

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

## Creating a new AI module

You can use the **Jupyter AI Module Cookiecutter** to create a new AI module easily. The AI module constructed from the template serves as a very simple example that can be extended however you wish. 

First, install `cookiecutter`.

```
pip install cookiecutter
```

Then, from the root of your `jupyter-ai` repository, run these commands:

```
cd packages/
cookiecutter jupyter-ai-module-cookiecutter
```

Follow the prompts to create a new AI module under `packages/`. Your labextension name should use hyphens, whereas your Python name should use underscores.

To integrate the new AI module into the Jupyter AI monorepo, run this command from the AI module root:

```
rm -r .github/ binder/ CHANGELOG.md RELEASE.md
```

Rename the JS package to be scoped under `@jupyter-ai/`.

Finally, add the Python package to the `options.python_packages` field in `.jupyter-releaser.toml`.

## Making changes while your server is running

If you change, add, or remove a **magic command**, after rebuilding, restart the kernel
or restart the server.

If you change the **server implementation** of an AI module, after rebuilding, restart the server.

If you make changes to the **user interface** or **lab extension**, run `jlpm build` and then
refresh your browser tab. Make sure to run `jlpm setup:dev` after starting a new Hatch shell.

## Development uninstall

To uninstall your Jupyter AI development environment, remove the Hatch environment:

```
hatch env remove default
```
