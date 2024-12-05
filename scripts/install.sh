#!/bin/bash
set -eux

# Install JupyterLab
#
# Excludes v4.3.2 as it pins `httpx` to a very narrow range, causing `pip
# install` to stall on package resolution.
#
# See: https://github.com/jupyterlab/jupyter-ai/issues/1138
pip install jupyterlab~=4.0,!=4.3.2

# Install core packages
cp playground/config.example.py playground/config.py
jlpm install
jlpm dev-install

# install docs packages
pip install sphinx
pip install -r docs/requirements.txt
