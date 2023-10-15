# Debug / Install

## Clone
Both projects must be in the same directory

```shell
# jupyterlab
git clone git@github.com:krassowski/jupyterlab.git
cd jupyterlab
git checkout inline-completion-api
```

```shell
# jupyter-ai-bigcode-code-completion
git clone git@github.com:Wzixiao/jupyter-ai-bigcode-code-completion.git
cd jupyter-ai-bigcode-code-completion
git checkout inline-api-shortcut
```

## Install
You must execute the first one before executing the second one.

And the two projects must be in the same virtual environment.

```shell
# jupyterlab
cd jupyterlab
pip install -e ".[dev,test]"
jlpm install
jlpm run build  # Build the dev mode assets (optional)
```

```shell
# jupyter-ai-bigcode-code-completion
cd jupyter-ai-bigcode-code-completion
./script/shell.sh
```

## Start up

```shell
# jupyterlab
cd jupyterlab
jupyter lab --dev-mode --watch --extensions-in-dev-mode
```

## Debug / Develop

```shell
# jupyter-ai-bigcode-code-completion
npm run watch
```
