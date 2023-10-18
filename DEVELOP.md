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


# Develop document

## Key Press
The handling of key presses is achieved by adding keyboard event handlers to the **CodeMirror** instance object of a cell when switching between cells. The reason for using this approach:
It allows selective triggering of the original functions based on the key pressed by the user. Adding keyboard responses to general DOM often can't achieve this.

## Completion
When loading the extension, it fetches **ICompletionProviderManager** as well as my own implementation of **BigcodeInlineCompletionProvider**.

When the user presses the request shortcut key, the **invoke** function of **ICompletionProviderManager** is triggered, pressing enter will trigger the **accept** function.

The reason for exposing **BigcodeInlineCompletionProvider**:
We need some variables to complete the overall logic, such as:

1. When the stream is ongoing, and the user presses a character that matches what the LLM service provider returns, the stream is terminated and returns the insert_text filtered based on user input.
2. When the stream is ongoing and the user presses the shortcut key (Enter) that triggers the accept function, we need to terminate this request. Additionally, we require variables from **BigcodeInlineCompletionProvider** to determine whether to accept. If the user isn't making a llm request, then it retains the keyboard's original function.


When automatic requests are triggered (i.e., context.triggerKind === 1):

If the stream is ongoing, it will terminate the stream and return an item that has undergone filtering. If the stream is not ongoing, it returns an empty array.

## Network request
For now, the requests are sent directly from the front end to the LLM server. Should we integrate this into the Bigcode backend server? (To improve user experience, the token needs to be securely stored.)

