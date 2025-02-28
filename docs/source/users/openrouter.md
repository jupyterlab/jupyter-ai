# Using OpenRouter or OpenAI Interfaces in Jupyter AI

[(Return to the Chat Interface page)](index.md#openrouter-usage)

For models that are compatible with the OpenAI library, Jupyter AI provides configuration via OpenRouter. By supporting the configuration of parameters such as the api_key, base_url, and model, various large model services compatible with the OpenAI library call methods can be used. For more details on OpenRouter as a unified interface for LLMs, see https://openrouter.ai/.

As an example, we walk through the steps needed to use models from [Deepseek](https://www.deepseek.com) via the OpenRouter provider. If you do not have `langchain-openai` installed, please install it and restart JupyterLab. This is necessary as it provides the SDK for accessing any OpenAI API.

First, navigate to the `AI Settings` pane via the AI settings button in `v2` or via the dropdown in `v3` of Jupyter AI, as shown below:

<img src="../_static/ai-settings.png"
    width="75%"
    alt='Screenshot of the dropdown where AI Settings is chosen and it opens tab in Jupyter AI where models are selected.'
    class="screenshot" />

Second, select the `OpenRouter :: *` model provider in the Jupyter AI settings. If you don't see this, please verify that you have installed `langchain-openai` and that you are using `jupyter_ai>=2.24.0`. Be sure to restart JupyterLab after upgrading or installing either package.

Jupyter AI's settings page with the OpenRouter provider selected is shown below:

<img src="../_static/openrouter-model-setup.png"
    width="75%"
    alt='Screenshot of the tab in Jupyter AI where OpenRouter model access is selected.'
    class="screenshot" />

Type in the model name and the API base URL corresponding to the model you wish to use. For Deepseek, you should use `https://api.deepseek.com` as the API base URL, and use `deepseek-chat` as the local model ID.

If you are using OpenRouter for the first time it will also require entering the `OPENROUTER_API_KEY`. If you have used OpenRouter before with a different model provider, you will need to update the API key. After doing this, click "Save Changes" at the bottom to save your settings.

You should now be able to use Deepseek! An example of usage is shown next:

<img src="../_static/openrouter-chat.png"
    width="75%"
    alt='Screenshot of chat using Deepseek via the OpenRouter provider.'
    class="screenshot" />

In a similar manner, models may also be invoked directly using the OpenAI provider interface in Jupyter AI. First, you can choose the OpenAI provider and then enter in the model ID, as shown on the OpenAI [models page](https://platform.openai.com/docs/models). An example is shown below:

<img src="../_static/openai-chat-openai.png"
    width="75%"
    alt='Screenshot of chat using gpt-4o via the OpenAI provider.'
    class="screenshot" />

DeepSeek models may be used via the same interface, if the base API url is provided:

<img src="../_static/openai-chat-deepseek.png"
    width="75%"
    alt='Screenshot of chat using deepseek via the OpenAI provider.'
    class="screenshot" />

For DeepSeek models, enter the DeepSeek API for the OpenAI API key.

Models deployed using vLLM may be used in a similar manner:

<img src="../_static/openai-chat-vllm.png"
    width="75%"
    alt='Screenshot of chat using vllm via the OpenAI provider.'
    class="screenshot" />

Usage of models using vLLM and their deployment is discussed [here](vllm.md).

For embedding models from OpenAI, you can generically choose them using the AI Settings interface as well:

<img src="../_static/openai-embeddings.png"
    width="75%"
    alt='Screenshot of embedding use via the OpenAI provider.'
    class="screenshot" />

[(Return to the Chat Interface page)](index.md#openrouter-usage)
