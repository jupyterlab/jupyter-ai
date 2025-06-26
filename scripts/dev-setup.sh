#!/bin/bash
#
# Development setup script for contributors.

set -eu

# Detect available Python environment manager (micromamba > mamba > conda)
# command -v checks if a command exists in PATH and is executable (POSIX compliant)
ENV_MANAGER=""
if command -v micromamba >/dev/null 2>&1; then
    ENV_MANAGER="micromamba"
elif command -v mamba >/dev/null 2>&1; then
    ENV_MANAGER="mamba"
elif command -v conda >/dev/null 2>&1; then
    ENV_MANAGER="conda"
else
    echo "Error: No Python environment manager found!"
    echo "Please install one of the following: micromamba, mamba, or conda"
    echo "  - micromamba: https://micromamba.readthedocs.io/en/latest/installation.html"
    echo "  - mamba: https://mamba.readthedocs.io/en/latest/installation.html"
    echo "  - conda: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "Using environment manager: $ENV_MANAGER"

# Create `jaidev` environment if it does not exist
if ! $ENV_MANAGER env list | grep -q "jaidev"; then
    echo "No Jupyter AI development environment named 'jaidev' found."
    echo "Creating 'jaidev' environment..."
    $ENV_MANAGER env create -f dev-environment.yml -y
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Error: Failed to create 'jaidev' environment. Exiting."
        exit $exit_code
    fi
fi


# Run environment manager shell hook. This is required for
# `activate`/`deactivate` commands to work in scripts
eval "$($ENV_MANAGER shell hook --shell bash)"

# Activate `jaidev` environment
echo "Activating Jupyter AI development environment 'jaidev'..."
$ENV_MANAGER activate jaidev

# Install JS dependencies
echo "Installing NPM dependencies..."
jlpm install

# Build JS assets
echo "Building JavaScript assets..."
jlpm build

# Perform editable installation of `jupyter-ai` and `jupyter-ai-magics` locally
echo "Running editable installation..."
jlpm dev:install

# Install documentation packages
echo "Installing documentation build requirements..."
uv pip install sphinx
uv pip install -r docs/requirements.txt

# Copy example config to `playground/` dir
cp playground/config.example.py playground/config.py

echo "The Jupyter AI development environment 'jaidev' is ready!"
echo "Run 'jupyter lab' to start the JupyterLab server and test your development build of Jupyter AI."
echo "Remember to run '{conda,mamba,micromamba} activate jaidev' each time you begin development from a new terminal."
echo "See the contributor documentation for more help: https://jupyter-ai.readthedocs.io/en/latest/contributors/index.html"
