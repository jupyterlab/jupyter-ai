# Jupyter AI

**Jupyter AI** is a package that lets Jupyter notebook users run tasks using generative AI (GAI) using APIs provided by GAI model vendors.

Jupyter AI provides a framework for AI modules that define GAI-powered tasks. For example, a "generate code" task uses a large language model (LLM) to generate source code from a text description, and an "explain code" task could use that same LLM to provide a plain English explanation for what some source code does. AI modules can read and write text, images, or other media formats, and can work on multiple file types — not just Jupyter notebooks. AI modules are Python packages that provide GAI interfaces and can provide JupyterLab extensions as well. They can register new models, new insertion modes, and new tasks. You can use the `%%ai` magic command to start a task.

## Contents

```{toctree}
---
maxdepth: 2
---

users/index
contributors/index
```