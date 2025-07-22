from litellm import all_embedding_models, models_by_provider

chat_model_ids = []
embedding_model_ids = []
embedding_model_set = set(all_embedding_models)

for provider_name in models_by_provider:
    for model_name in models_by_provider[provider_name]:
        model_name: str = model_name

        if model_name.startswith(f"{provider_name}/"):
            model_id = model_name
        else:
            model_id = f"{provider_name}/{model_name}"

        is_embedding = (
            model_name in embedding_model_set
            or model_id in embedding_model_set
            or "embed" in model_id
        )

        if is_embedding:
            embedding_model_ids.append(model_id)
        else:
            chat_model_ids.append(model_id)


CHAT_MODELS = sorted(chat_model_ids)
"""
List of chat model IDs, following the `litellm` syntax.
"""

EMBEDDING_MODELS = sorted(embedding_model_ids)
"""
List of embedding model IDs, following the `litellm` syntax.
"""
