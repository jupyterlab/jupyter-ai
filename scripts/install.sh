#!/bin/bash

pip install jupyterlab
cp playground/config.example.py playground/config.py
jlpm install
jlpm dev-install

if [[ $(uname -m) == 'arm64' ]]; then
    pip uninstall grpcio && conda install -y grpcio
fi
