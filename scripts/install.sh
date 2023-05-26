#!/bin/bash

# install core packages
pip install jupyterlab~=3.0
cp playground/config.example.py playground/config.py
jlpm install
jlpm dev-install

# install docs packages
pip install sphinx
pip install -r docs/requirements.txt

# install grpcio via conda for ARM platforms to preserve compatibility with Ray
if [[ $(uname -m) == 'arm64' ]]; then
    pip uninstall grpcio && conda install -y grpcio
fi
