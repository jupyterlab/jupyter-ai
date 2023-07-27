#!/bin/bash

# install core packages
pip install jupyterlab~=4.0
cp playground/config.example.py playground/config.py
jlpm install
jlpm dev-install

# install docs packages
pip install sphinx
pip install -r docs/requirements.txt
