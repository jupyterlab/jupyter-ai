#!/bin/bash
#
# Setup script used to initialize CI environments in GitHub workflows.
# Not intended for human use.
#
# NOTE: this script requires the `astral-sh/setup-uv` GitHub action to run
# before being called in a GitHub workflow. See this page for more guidance on
# running `uv` inside a GitHub workflow:
# https://docs.astral.sh/uv/guides/integration/github/

set -eux

# Install JupyterLab
uv pip install "jupyterlab>=4.4"

# Build & install packages
jlpm install
jlpm build
jlpm dev:install
