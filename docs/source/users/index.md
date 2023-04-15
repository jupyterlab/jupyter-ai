# Users

Welcome to the user documentation for Jupyter AI. If you are interested in contributing a new or modified
feature in JupyterLab, please see our {doc}`contributor's guide </contributors/index>`.

## Model providers

Jupyter AI supports a wide range of model providers and models. To use Jupyter AI, you will need to 
install the corresponding Python package and configure the API key (or other authenication credentials) for the provider. 
You can find the environment variables you need to set, and the Python packages you need, in
[`packages/jupyter-ai/jupyter_ai/providers.py`](https://github.com/jupyterlab/jupyter-ai/blob/main/packages/jupyter-ai/jupyter_ai/providers.py).

Jupyter AI supports the following model providers:

| Provider            | Provider ID          | Environment variable       | Python package(s)               |
|---------------------|----------------------|----------------------------|---------------------------------|
| AI21                | `ai21`               | `AI21_API_KEY`             | `ai21`                          |
| Anthropic           | `anthropic`          | `ANTHROPIC_API_KEY`        | `anthropic`                     |
| Cohere              | `cohere`             | `COHERE_API_KEY`           | `cohere`                        |
| HuggingFace Hub     | `huggingface_hub`    | `HUGGINGFACEHUB_API_TOKEN` | `huggingface_hub`, `ipywidgets` |
| OpenAI              | `openai`             | `OPENAI_API_KEY`           | `openai`                        |
| OpenAI (chat)       | `openai-chat`        | `OPENAI_API_KEY`           | `openai`                        |
| SageMaker Endpoints | `sagemaker-endpoint` | N/A                        | `boto3`                         |

To use SageMaker's models, you will need to authenticate via
[boto3](https://github.com/boto/boto3).

For example, to use OpenAI models, install the necessary package, and set an environment
variable when you start JupyterLab from a terminal:

```bash
pip install openai
OPENAI_API_KEY=your-api-key-here jupyter lab
```

:::{attention}
:name: open-ai-cost
Model providers may charge users for API usage. Jupyter AI users are
responsible for all charges they incur when they make API requests. Review your model
provider's pricing information before submitting requests via Jupyter AI.
:::

## Installing

To use Jupyter AI, you will need to have JupyterLab ≥ 3.5 (*not* JupyterLab 4) installed.

If you want to install both the `%%ai` magic and the JupyterLab extension, you can run:

    $ pip install jupyter_ai

If you are not using JupyterLab and only want to install the Jupyter AI `%%ai` magic you can run:

    $ pip install jupyter_ai_magics

The `%%ai` magic will work anywhere the IPython kernel runs (JupyterLab, Jupyter Notebook, Google Colab, VSCode, etc.).

You can check that the Jupyter AI server extension is enabled by running:

```bash
jupyter server extension list
```

To verify that the frontend extension is installed, run:

```bash
jupyter labextension list
```

To remove the extension, run:

```bash
pip uninstall jupyter_ai
```

or

```bash
pip uninstall jupyter_ai_magics
```


## The Jupyter AI `%%ai` magic command

The examples in this section are based on the [Jupyter AI example notebook](https://github.com/jupyterlab/jupyter-ai/blob/main/examples/magics.ipynb).

Before you send your first prompt to an AI model, load the IPython extension by running 
the following code in a notebook cell or IPython shell:

```
%load_ext jupyter_ai
```

This command should not produce any output.

The `%%ai` magic command is easy to use and enables to to quickly pick which model you want to use
and specify natural language prompts.

### Choosing a provider and model

To use Jupyter AI, use the `%%ai` cell magic with the
syntax `<provider-id>:<model-id>`. Your prompt starts on the second line of the cell.
The prompt starts on the second line of the cell.

For example, to send a text prompt to the provider `anthropic` and the model ID
`claude-v1.2`, enter the following code into a cell and run it:

```
%%ai anthropic:claude-v1.2
Write a poem about C++.
```

We support the following providers, and all model IDs for each of these
providers, as defined in [`langchain.llms`](https://langchain.readthedocs.io/en/latest/reference/modules/llms.html#module-langchain.llms):

- `ai21`
- `anthropic`
- `cohere`
- `huggingface_hub`
- `openai`
- `openai-chat`
- `sagemaker-endpoint`

If your model ID is associated with only one provider, you can omit the `provider-id` and
the colon from the first line. For example, because `ai21` is the only provider of the
`j2-jumbo-instruct` model, these two code cells will do the same thing when you run them:

```
%%ai ai21:j2-jumbo-instruct
Write some JavaScript code that prints "hello world" to the console.
```

```
%%ai j2-jumbo-instruct # infers AI21 provider
Write some JavaScript code that prints "hello world" to the console.
```

### Formatting the output

By default, Jupyter AI assumes that a model will output markdown, so the output of
an `%%ai` command will be formatted as markdown by default. You can override this
using the `-f` or `--format` argument to your magic command. Valid formats include:

- `code`
- `markdown`
- `math`
- `html`
- `json`
- `text`

For example, to force the output of a command to be interpreted as HTML, you can run:

```
%%ai anthropic:claude-v1.2 -f html
Create a square using SVG with a black border and white fill.
```

The following cell will produce output in IPython's `Math` format, which in a web browser
will look like properly typeset equations.

```
%%ai chatgpt -f math
Generate the 2D heat equation in LaTeX surrounded by `$$`. Do not include an explanation.
```

This prompt will produce output as a code cell below the input cell. 

:::{warning}
:name: run-code
**Please review any code that a generative AI model produces before you run it
or distribute it.**
The code that you get in response to a prompt may have negative side effects and may
include calls to nonexistent (hallucinated) APIs.
:::

```
%%ai chatgpt -f code
A function that computes the lowest common multiples of two integers, and
a function that runs 5 test cases of the lowest common multiple function
```

### Interpolating in prompts

Using curly brace syntax, you can include variables and other Python expressions in your
prompt. This lets you execute a prompt using code that the IPython kernel knows about,
but that is not in the current cell.

For example, we can set a variable in one notebook cell:

```python
poet = "Walt Whitman"
```

Then, we can use this same variable in an `%%ai` command in a later cell:

```
%%ai chatgpt
Write a poem in the style of {poet}
```

When this cell runs, `{poet}` is interpolated as `Walt Whitman`, or as whatever `poet`
is assigned to at that time.

You can use the special `In` and `Out` list with interpolation syntax to explain code
located elsewhere in a Jupyter notebook. For example, if you run the following code in
a cell, and its input is assigned to `In[11]`:

```python
for i in range(0, 5):
  print(i)
```

You can then refer to `In[11]` in an `%%ai` magic command, and it will be replaced
with the code in question:

```
%%ai cohere:command-xlarge-nightly
Please explain the code below:
--
{In[11]}
```

You can also refer to the cell's output using the special `Out` list, with the same index.

```
%%ai cohere:command-xlarge-nightly
Write code that would produce the following output:
--
{Out[11]}
```

Jupyter AI also adds the special `Err` list, which uses the same indexes as `In` and `Out`.
For example, if you run code in `In[3]` that produces an error, that error is captured in
`Err[3]` so that you can request an explanation using a prompt such as:

```
%%ai chatgpt
Explain the following Python error:
--
{Err[3]}
```

The AI model that you use will then attempt to explain the error. You could also write a
prompt that uses both `In` and `Err` to attempt to get an AI model to correct your code:

```
%%ai chatgpt --format code
The following Python code:
--
{In[3]}
--
produced the following Python error:
--
{Err[3]}
--
Write a new version of this code that does not produce that error.
```

