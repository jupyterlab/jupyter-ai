# jupyter-ai

[![Github Actions Status](https://github.com/jupyterlab/jupyter_ai/workflows/Build/badge.svg)](https://github.com/jupyterlab/jupyter_ai/actions/workflows/build.yml)
A generative AI extension for JupyterLab

### Dev setup
```shell
hatch -e default shell # once, "exit" will escape from shell
jlpm run build # for each change
```

### Uninstall
```shell
hatch env remove default
```