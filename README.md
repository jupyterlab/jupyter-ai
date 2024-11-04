# Jupyter AI

**Jupyter AI is under incubation as part of the JupyterLab organization.**

Jupyter AI connects generative AI with Jupyter notebooks. Jupyter AI provides a user-friendly
and powerful way to explore generative AI models in notebooks and improve your productivity
in JupyterLab and the Jupyter Notebook. More specifically, Jupyter AI offers:

* An `%%ai` magic that turns the Jupyter notebook into a reproducible generative AI playground.
  This works anywhere the IPython kernel runs (JupyterLab, Jupyter Notebook, Google Colab, Kaggle, VSCode, etc.).
* A native chat UI in JupyterLab that enables you to work with generative AI as a conversational assistant.
* Support for a wide range of generative model providers, including AI21, Anthropic, AWS, Cohere,
  Gemini, Hugging Face, MistralAI, NVIDIA, and OpenAI.
* Local model support through GPT4All and Ollama, enabling use of generative AI models on consumer grade machines
  with ease and privacy.

Documentation is available on [ReadTheDocs](https://jupyter-ai.readthedocs.io/en/latest/).

![A screenshot of Jupyter AI showing the chat interface and the magic commands](docs/source/_static/jupyter-ai-screenshot.png)

## Requirements

You will need to have installed the following software to use Jupyter AI:

- Python 3.8 - 3.12
- JupyterLab 4 or Notebook 7

In addition, you will need access to at least one model provider.

> [!IMPORTANT]
> JupyterLab 3 reached its end of maintenance date on May 15, 2024. As a result, we will not backport new features to the v1 branch supporting JupyterLab 3. Fixes for critical issues will still be backported until December 31, 2024. If you are still using JupyterLab 3, we strongly encourage you to **upgrade to JupyterLab 4 as soon as possible**. For more information, see [JupyterLab 3 end of maintenance](https://blog.jupyter.org/jupyterlab-3-end-of-maintenance-879778927db2) on the Jupyter Blog.

## Setting Up Model Providers in a Notebook

To use any AI model provider within this notebook, you'll need the appropriate credentials, such as API keys.

Obtain the necessary credentials, such as API keys, from your model provider's platform.

You can set your keys using environment variables or in a code cell in your notebook.
In a code cell, you can use the %env magic command to set the credentials as follows:

```python
# NOTE: Replace 'PROVIDER_API_KEY' with the credential key's name,
# and replace 'YOUR_API_KEY_HERE' with the key.
%env PROVIDER_API_KEY=YOUR_API_KEY_HERE
```

For more specific instructions for each model provider, refer to [the model providers documentation](https://jupyter-ai.readthedocs.io/en/latest/users/index.html#model-providers).

## Installation

Below is a simplified overview of the installation and usage process.
See [our official documentation](https://jupyter-ai.readthedocs.io/en/latest/users/index.html)
for details on installing and using Jupyter AI.

### Quick installation via `pip` (recommended)

If you want to install both the `%%ai` magic and the JupyterLab extension, you can run:

    $ pip install jupyter-ai[all]

Then, restart JupyterLab. This will install every dependency, which will give you access to all models currently supported by `jupyter-ai`. 

If you are not using JupyterLab and you only want to install the Jupyter AI `%%ai` magic, you can run:

    $ pip install jupyter-ai-magics[all]

`jupyter-ai` depends on `jupyter-ai-magics`, so installing `jupyter-ai` automatically installs `jupyter-ai-magics`.

If you do not run install with the `[all]` option, you may need to install third-party packages to use some model providers and some file formats with Jupyter AI. For example, to use OpenAI models, in addition to your current install also run

```
pip install langchain-openai
```

To use models from Anthropic, install:

```
pip install langchain-anthropic
```

After these installs you should see the OpenAI and Anthropic models in the drop down list. If you are using Claude models on AWS Bedrock, you must also install

```
pip install langchain-aws
```

Similarly, install `langchain-<provider>` packages for other providers as well. For more information on model providers and which dependencies they require, see [the model provider table](https://jupyter-ai.readthedocs.io/en/latest/users/index.html#model-providers).

### Minimal installation via `pip` (optional)

Most model providers in Jupyter AI require a specific dependency to be installed before they are available for use. These are called _provider dependencies_. Provider dependencies are optional to Jupyter AI, meaning that Jupyter AI can be installed with or without any provider dependencies installed.

If a provider requires a dependency that is not installed, its models are not listed in the user interface which allows you to select a language model. This offers a way for users to control which models are available in your Jupyter AI environment.

For example, to install Jupyter AI with only added support for Anthropic models, run:

```
pip install jupyter-ai langchain-anthropic
```

### With conda

As an alternative to using `pip`, you can install `jupyter-ai` using
[Conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)
from the `conda-forge` channel, using one of the following two commands:

    $ conda install -c conda-forge jupyter-ai  # or,
    $ conda install conda-forge::jupyter-ai

Most model providers in Jupyter AI require a specific dependency to be installed before they are available for use. These provider dependencies are not installed by default when installing `jupyter-ai` from Conda Forge, and should be installed separately as needed.

For example, to install Jupyter AI with support for OpenAI models, run:

```
conda install conda-forge::jupyter-ai conda-forge::langchain-openai
```

For more information on model providers and which dependencies they require, see [the model provider table](https://jupyter-ai.readthedocs.io/en/latest/users/index.html#model-providers).

## The `%%ai` magic command

The `%%ai` magic works anywhere the IPython kernel runs, including JupyterLab, Jupyter Notebook, Google Colab, and Visual Studio Code.

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
