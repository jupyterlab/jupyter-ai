# Getting Started

Welcome to Jupyter AI, which brings generative AI to Jupyter. Jupyter AI provides a user-friendly
and powerful way to explore generative AI models in notebooks and improve your productivity
in JupyterLab and the Jupyter Notebook. More specifically, Jupyter AI offers:

- A native chat UI in JupyterLab that enables you to work with generative AI as a conversational assistant, and also enables interaction with the active notebook.
- An `%%ai` magic that turns the Jupyter notebook into a reproducible generative AI playground.
  This works anywhere the IPython kernel runs (JupyterLab, Jupyter Notebook, Google Colab, VSCode, etc.).
- Support for a wide range of generative model providers and models
  (AI21, Amazon, Anthropic, Cohere, Gemini, Hugging Face, MistralAI, OpenAI, NVIDIA, etc.).
- Multiple editable chat threads are available, each thread saved to a separate Jupyter server document with extension `.chat`.
- Real time collaboration (RTC) is enabled in both chat and Jupyter notebook, if cloud deployments support it.
- Support for hundreds of LLMs from many additional providers.
- Chat personas with agentic capabilities, with a default `Jupyternaut` persona.

## JupyterLab Support

**Each major version of Jupyter AI supports _only one_ major version of JupyterLab.** Jupyter AI 1.x supports
JupyterLab 3.x, and Jupyter AI 2.x supports JupyterLab 4.x. The feature sets of versions 1.0.0 and 2.0.0
are the same. We will maintain support for JupyterLab 3 for as long as it remains maintained. Jupyter AI v3 supports JupyterLab 4.x.

The `main` branch of Jupyter AI targets the newest supported major version of JupyterLab. All new features and most bug fixes will be
committed to this branch. Features and bug fixes will be backported
to work on JupyterLab 3 only if developers determine that they will add sufficient value.
**We recommend that JupyterLab users who want the most advanced Jupyter AI functionality upgrade to JupyterLab 4.**

## Quickstart

It is best to install `jupyter-ai` in an environment. Use [conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html) to create an environment that uses Python 3.13 and the latest version of JupyterLab:

    $ conda create -n jupyter-ai python=3.13 jupyterlab
    $ conda activate jupyter-ai

To install both the `%%ai` magic and the JupyterLab extension, you can run:

    $ pip install jupyter-ai==<version number>

Choose the version number, the latest version is `3.0.0b9`.

For an installation with all related packages, use:

    $ pip install "jupyter-ai[all]"==<version number>

To start Jupyter AI in Jupyter Lab, run

```
jupyter lab
```

You should see an interface similar to the screenshot on the home page. Use the `+ Chat` button in the chat panel to open a chat thread and enter prompts. In the chat box enter `@` to see a list of personas, and you can select one before entering your query.

To connect a LLM for use in your chat threads you can select the `Settings` dropdown menu, select `Jupyternaut settings` in it to see the settings panel, in which you can select a chat model, specify model parameters if needed, and also add API keys for using LLMs that require it.

### Using uv

To use `uv` instead of `pip`:

Create a virtual environment with `uv` in any folder:

```
uv venv --python 3.13
```

Activate the environment:

```
source .venv/bin/activate
```

Install with

```
uv pip install "jupyter-ai[all]"==<version number>
```

Run with

```
jupyter lab
```

## Next Steps

- See the full {doc}`User Guide </users/index>` for detailed documentation on all features.
- See the {doc}`Contributor's Guide </contributors/index>` if you want to help build Jupyter AI.
- See the {doc}`Developer's Guide </developers/index>` if you want to extend Jupyter AI with custom providers or personas.
