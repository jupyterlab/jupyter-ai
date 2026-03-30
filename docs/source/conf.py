# Configuration file for the Sphinx documentation builder.

import time

project = "Jupyter AI"
copyright = f"© 2023–{time.localtime().tm_year}, Project Jupyter"
author = "Project Jupyter"
html_title = "Jupyter AI"

# -- General configuration ---------------------------------------------------

extensions = ["myst_parser", "sphinx_design", "sphinx_tabs.tabs"]
myst_enable_extensions = ["colon_fence"]

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = "shibuya"
html_static_path = ["_static"]

html_css_files = [
    "css/custom.css",
]

html_logo = "_static/jupyter_logo.png"

html_theme_options = {
    "accent_color": "orange",
    "github_url": "https://github.com/jupyterlab/jupyter-ai",
    "nav_links": [
        {
            "title": "Users",
            "url": "users/index",
        },
        {
            "title": "Contributors",
            "url": "contributors/index",
        },
        {
            "title": "Developers",
            "url": "developers/index",
        },
    ],
}
