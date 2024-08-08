# Using Amazon Bedrock with Jupyter AI

[**<--Back**](index.md#amazon-bedrock-usage)

Bedrock supports many language model providers such as AI21 Labs, Amazon, Anthropic, Cohere, Meta, and Mistral AI. To use the base models from any supported provider make sure to enable them in Amazon Bedrock by using the AWS console. Go to Amazon Bedrock and select `Model Access` as shown here:

<img src="../_static/bedrock-model-access.png"
    width="75%"
    alt='Screenshot of the left panel in the AWS console where Bedrock model access is provided.'
    class="screenshot" />

Click through on `Model Access` and follow the instructions to grant access to the models you wish to use, as shown below. Make sure to accept the end user license (EULA) as required by each model. You may need your system administrator to grant access to your account if you do not have authority to do so.

<img src="../_static/bedrock-model-select.png"
    width="75%"
    alt='Screenshot of the Bedrock console where models may be selected.'
    class="screenshot" />

You should also select embedding models in addition to language completion models if you intend to use retrieval augmented generation (RAG) on your documents.

You may now select a chosen Bedrock model from the drop-down menu box title `Completion model` in the chat interface. If RAG is going to be used then pick an embedding model that you chose from the Bedrock models as well. An example of these selections is shown below:

<img src="../_static/bedrock-chat-basemodel.png"
    width="50%"
    alt='Screenshot of the Jupyter AI chat panel where the base language model and embedding model is selected.'
    class="screenshot" />

Bedrock also allows custom models to be trained from scratch or fine-tuned from a base model. Jupyter AI enables a custom model to be called in the chat panel using its `arn` (Amazon Resource Name). As with custom models, you can also call a base model by its `model id` or its `arn`. An example of using a base model with its `model id` through the custom model interface is shown below:

<img src="../_static/bedrock-chat-basemodel-modelid.png"
    width="75%"
    alt='Screenshot of the Jupyter AI chat panel where the base model is selected using model id.'
    class="screenshot" />

An example of using a base model using its `arn` through the custom model interface is shown below:

<img src="../_static/bedrock-chat-basemodel-arn.png"
    width="75%"
    alt='Screenshot of the Jupyter AI chat panel where the base model is selected using its ARN.'
    class="screenshot" />

To train a custom model in Amazon Bedrock, select `Custom models` in the Bedrock console as shown below, and then you may customize a base model by fine-tuning it or continuing to pre-train it:

<img src="../_static/bedrock-custom-models.png"
    width="75%"
    alt='Screenshot of the Bedrock custom models access in the left panel of the Bedrock console.'
    class="screenshot" />

For details on fine-tuning a base model from Bedrock, see this [reference](https://aws.amazon.com/blogs/aws/customize-models-in-amazon-bedrock-with-your-own-data-using-fine-tuning-and-continued-pre-training/); with related [documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/custom-models.html).

Once the model is fine-tuned, it will have its own `arn`, as shown below:

<img src="../_static/bedrock-finetuned-model.png"
    width="75%"
    alt='Screenshot of the Bedrock fine-tuned model ARN in the Bedrock console.'
    class="screenshot" />

As seen above, you may click on `Purchase provisioned throughput` to buy inference units with which to call the custom model's API. Enter the model's `arn` in Jupyter AI's Language model user interface to use the provisioned model.

[**<--Back**](index.md#amazon-bedrock-usage)
