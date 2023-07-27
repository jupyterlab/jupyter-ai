# Jupyter AI

Welcome to Jupyter AI, which brings generative AI to Jupyter. Jupyter AI provides a user-friendly
and powerful way to explore generative AI models in notebooks and improve your productivity
in JupyterLab and the Jupyter Notebook. More specifically, Jupyter AI offers:

* An `%%ai` magic that turns the Jupyter notebook into a reproducible generative AI playground.
  This works anywhere the IPython kernel runs (JupyterLab, Jupyter Notebook, Google Colab, VSCode, etc.).
* A native chat UI in JupyterLab that enables you to work with generative AI as a conversational assistant.
* Support for a wide range of generative model providers and models
  (AI21, Anthropic, Cohere, Hugging Face, OpenAI, SageMaker, etc.).

## JupyterLab support

**Each major version of Jupyter AI supports *only one* major version of JupyterLab.** Jupyter AI 1.x supports
JupyterLab 3.x, and Jupyter AI 2.x supports JupyterLab 4.x. The feature sets of versions 1.0.0 and 2.0.0
are the same. We will maintain support for JupyterLab 3 for as long as it remains maintained.

The `main` branch of Jupyter AI targets the newest supported major version of JupyterLab. All new features and most bug fixes will be
committed to this branch. Features and bug fixes will be backported
to work on JupyterLab 3 only if developers determine that they will add sufficient value.
**We recommend that JupyterLab users who want the most advanced Jupyter AI functionality upgrade to JupyterLab 4.**

## Contents

```{toctree}
---
maxdepth: 2
---

users/index
contributors/index
```
