# Developers

This section describes the **developer API** in Jupyter AI that other Python packages can use to tailor Jupyter AI to their use-case. For example, developers can add new personas to Jupyter AI using the `jupyter-ai-jupyternaut` extension as a reference. 
<!-- Here are some examples of what other packages can do with the developer API: -->

<!-- - Add custom AI personas to Jupyter AI

- Add custom model providers to Jupyter AI -->

The developer API allows other packages to modify both the frontend & the backend. The developer API has two parts: the **Entry points API** and the **Lumino plugin API** (currently unused, but planned for v3).

- The Entry points API allows packages to add certain objects to Jupyter AI's backend. This is available to any Python package.

- The Lumino plugin API allows packages to add to, modify, or even override parts of Jupyter AI's frontend. This is only available to labextension packages.

<!-- ```{toctree} Table of Contents
:depth: 3

entry_points_api/index.md
``` -->

In v3, `jupyter-ai` is no longer a monorepo. Instead it comprises components that can be composed together to support a wide range of AI-assisted workflows, from code generation and data analysis to interactive learning and research. These components are located in the `jupyter-ai-contrib` org with multiple repositories, each representing a submodule that is installed along with `jupyter-ai`. For details, refer to the documentation on [Development Setup](https://jupyter-ai.readthedocs.io/en/v3/contributors/index.html#development-setup). Also refer to the related repositories' README files for overview. 