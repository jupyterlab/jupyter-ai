#!/bin/bash
#
# Setup script used to initialize CI environments in GitHub workflows.
# Not intended for human use.

set -eux

# Install JupyterLab
pip install "jupyterlab>=4.4"

# Build & install packages
jlpm install
jlpm build
jlpm dev-install
