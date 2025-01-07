# Using OpenRouter in Jupyter AI

[(Return to the Chat Interface page)](index.md#openrouter-usage)

For models that are compatible with the OpenAI library, Jupyter AI provides configuration via OpenRouter. By supporting the configuration of parameters such as the api_key, base_url, and model, various large model services compatible with the OpenAI library call methods can be used. For more details on OpenRouter as a unified interface for LLMs, see https://openrouter.ai/. 

As an example, we walk through the steps needed to use models from [Deepseek](https://www.deepseek.com) via the OpenRouter provider. If you do not have `langchain-openai` installed, please install it and restart JupyterLab. This is necessary as it provides the SDK for accessing any OpenAI API.

First, open the `AI Settings` page in a new tab as shown:

<img src="../_static/ai-settings.png"
    width="75%"
    alt='Screenshot of the dropdown where AI Settings is chosen and it opens tab in Jupyter AI where models are selected.'
    class="screenshot" />

Second, Select the `OpenRouter :: *` model in the Jupyter AI settings. (If you don't see this, please upgrade to at least the latest version of Jupyter AI v2.) The `AI Settings` tab in v3 of Jupyter AI is shown below:

<img src="../_static/openrouter-model-setup.png"
    width="75%"
    alt='Screenshot of the tab in Jupyter AI where OpenRouter model access is selected.'
    class="screenshot" />

Type in the local model name and the API base URL corresponding to the model you wish to use. For Deepseek, you should use https://api.deepseek.com as the API base URL, and use `deepseek-chat` as the local model ID. 

If you are using OpenRouter for the first time it will also require entering the `OPENROUTER_API_KEY`. If you have used OpenRouter before with a different model provider, you will need to update the API key. After doing this, click "Save Changes" at the bottom to save your settings. 

You should now be able to use Deepseek! An example of usage is shown next:

<img src="../_static/openrouter-chat.png"
    width="75%"
    alt='Screenshot of chat using Deepseek via the OpenRouter provider.'
    class="screenshot" />

[(Return to the Chat Interface page)](index.md#openrouter-usage)
