# Jupyter AI

Welcome to Jupyter AI, which brings generative AI to Jupyter. Jupyter AI provides a user-friendly
and powerful way to explore generative AI models in notebooks and improve your productivity
in JupyterLab and the Jupyter Notebook. More specifically, Jupyter AI offers:

* An `%%ai` magic that turns the Jupyter notebook into a reproducible generative AI playground.
  This works anywhere the IPython kernel runs (JupyterLab, Jupyter Notebook, Google Colab, VSCode, etc.).
* A native chat UI in JupyterLab that enables you to work with generative AI as a conversational assistant.
* Support for a wide range of generative model providers and models
  (AI21, Anthropic, Cohere, Hugging Face, OpenAI, SageMaker, etc.).

Documentation is available on [ReadTheDocs](https://jupyter-ai.readthedocs.io/en/latest/).

## Requirements

- Python 3.8 - 3.11
- JupyterLab 4

## Installation

Below is a simplified overview of the installation and usage process.
See [our official documentation](https://jupyter-ai.readthedocs.io/en/latest/users/index.html)
for details on installing and using Jupyter AI.

### With pip

If you want to install both the `%%ai` magic and the JupyterLab extension, you can run:

    $ pip install jupyter_ai

If you are not using JupyterLab and you only want to install the Jupyter AI `%%ai` magic, you can run:

    $ pip install jupyter_ai_magics


### With conda

First, install
[conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)
and create an environment that uses Python 3.11:

    $ conda create -n jupyter-ai python=3.11
    $ conda activate jupyter-ai
    $ pip install jupyter_ai

If you are not using JupyterLab and you only want to install the Jupyter AI `%%ai` magic, skip the `pip install jupyter_ai` step above, and instead, run:

    $ pip install jupyter_ai_magics


## The `%%ai` magic command

The `%%ai` magic works anywhere the IPython kernel runs (JupyterLab, Jupyter Notebook, Google Colab, Visual Studio Code, etc.).

Once you have installed the `%%ai` magic, you can enable it in any notebook or the IPython shell by running:

    %load_ext jupyter_ai_magics

or:

    %load_ext jupyter_ai

The screenshots below are from notebooks in the `examples/` directory of this package.

Then, you can use the `%%ai` magic command to specify a model and natural language prompt:

![Sample with code generation](./docs/source/_static/sample-code.png)

Jupyter AI can also generate HTML and math to be rendered as cell output.

![Sample with HTML and math generation](./docs/source/_static/sample-html-math.png)

Jupyter AI can interpolate IPython expressions, allowing you to run prompts
that include variable values.

![Sample with code interpolation and markdown output](./docs/source/_static/sample-markdown.png)

## JupyterLab extension

The Jupyter AI extension for JupyterLab offers a native UI that enables multiple users
to chat with the Jupyter AI conversational assistant. If you have JupyterLab installed,
this should be installed and activated when you install the `jupyter_ai` package.

## Using

For help with installing and using Jupyter AI, please see our
[user documentation on ReadTheDocs](https://jupyter-ai.readthedocs.io/en/latest/users/index.html).

## Contributing

If you would like to contribute to Jupyter AI, see our
[contributor documentation on ReadTheDocs](https://jupyter-ai.readthedocs.io/en/latest/contributors/index.html).
