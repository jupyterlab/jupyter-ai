import json
import logging
import os
from unittest.mock import mock_open, patch

import pytest
from jupyter_ai.config_manager import (
    AuthError,
    ConfigManager,
    KeyInUseError,
    WriteConflictError,
)
from jupyter_ai.models import DescribeConfigResponse, GlobalConfig, UpdateConfigRequest
from jupyter_ai_magics.utils import get_em_providers, get_lm_providers
from langchain.pydantic_v1 import ValidationError


@pytest.fixture
def config_path(jp_data_dir):
    return str(jp_data_dir / "config.json")


@pytest.fixture
def schema_path(jp_data_dir):
    return str(jp_data_dir / "config_schema.json")


@pytest.fixture
def common_cm_kwargs(config_path, schema_path):
    """Kwargs that are commonly used when initializing the CM."""
    log = logging.getLogger()
    lm_providers = get_lm_providers()
    em_providers = get_em_providers()
    return {
        "log": log,
        "lm_providers": lm_providers,
        "em_providers": em_providers,
        "config_path": config_path,
        "schema_path": schema_path,
        "allowed_providers": None,
        "blocked_providers": None,
        "allowed_models": None,
        "blocked_models": None,
        "restrictions": {"allowed_providers": None, "blocked_providers": None},
        "defaults": {
            "model_provider_id": None,
            "embeddings_provider_id": None,
            "api_keys": None,
            "fields": None,
        },
    }


@pytest.fixture
def cm_kargs_with_defaults(config_path, schema_path, common_cm_kwargs):
    """Kwargs that are commonly used when initializing the CM."""
    log = logging.getLogger()
    lm_providers = get_lm_providers()
    em_providers = get_em_providers()
    return {
        **common_cm_kwargs,
        "defaults": {
            "model_provider_id": "bedrock-chat:anthropic.claude-v1",
            "embeddings_provider_id": "bedrock:amazon.titan-embed-text-v1",
            "api_keys": {"OPENAI_API_KEY": "open-ai-key-value"},
            "fields": {
                "bedrock-chat:anthropic.claude-v1": {
                    "credentials_profile_name": "default",
                    "region_name": "us-west-2",
                }
            },
        },
    }


@pytest.fixture
def cm(common_cm_kwargs):
    """The default ConfigManager instance, with an empty config and config schema."""
    return ConfigManager(**common_cm_kwargs)


@pytest.fixture
def cm_with_blocklists(common_cm_kwargs):
    kwargs = {
        **common_cm_kwargs,
        "blocked_providers": ["ai21"],
        "blocked_models": ["cohere:medium"],
    }
    return ConfigManager(**kwargs)


@pytest.fixture
def cm_with_allowlists(common_cm_kwargs):
    kwargs = {
        **common_cm_kwargs,
        "allowed_providers": ["ai21"],
        "allowed_models": ["cohere:medium"],
    }
    return ConfigManager(**kwargs)


@pytest.fixture
def cm_with_defaults(cm_kargs_with_defaults):
    """The default ConfigManager instance, with an empty config and config schema."""
    return ConfigManager(**cm_kargs_with_defaults)


@pytest.fixture(autouse=True)
def reset(config_path, schema_path):
    """Fixture that deletes the config and config schema after each test."""
    yield
    try:
        os.remove(config_path)
    except OSError:
        pass
    try:
        os.remove(schema_path)
    except OSError:
        pass


@pytest.fixture
def config_with_bad_provider_ids(tmp_path):
    """Fixture that creates a `config.json` with `model_provider_id` and  `embeddings_provider_id` values that would not associate with models. File is created in `tmp_path` folder. Function returns path to the file."""
    config_data = {
        "model_provider_id:": "foo:bar",
        "embeddings_provider_id": "buzz:fizz",
        "api_keys": {},
        "send_with_shift_enter": False,
        "fields": {},
    }
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as file:
        json.dump(config_data, file)
    return str(config_path)


@pytest.fixture
def cm_with_bad_provider_ids(common_cm_kwargs, config_with_bad_provider_ids):
    """Config manager instance created with `config_path` set to mocked `config.json` with `model_provider_id` and `embeddings_provider_id` values that would not associate with models."""
    common_cm_kwargs["config_path"] = config_with_bad_provider_ids
    return ConfigManager(**common_cm_kwargs)


def configure_to_cohere(cm: ConfigManager):
    """Configures the ConfigManager to use Cohere language and embedding models
    with the API key set. Returns a 3-tuple of the keyword arguments used."""
    LM_GID = "cohere:xlarge"
    EM_GID = "cohere:large"
    API_KEYS = {"COHERE_API_KEY": "foobar"}
    # the params use lowercase key names
    LM_LID = "xlarge"
    EM_LID = "large"
    API_PARAMS = {"cohere_api_key": "foobar"}
    req = UpdateConfigRequest(
        model_provider_id=LM_GID, embeddings_provider_id=EM_GID, api_keys=API_KEYS
    )
    cm.update_config(req)
    return LM_GID, EM_GID, LM_LID, EM_LID, API_PARAMS


def configure_to_openai(cm: ConfigManager):
    """Configures the ConfigManager to use OpenAI language and embedding models
    with the API key set. Returns a 3-tuple of the keyword arguments used."""
    LM_GID = "openai-chat:gpt-3.5-turbo"
    EM_GID = "openai:text-embedding-ada-002"
    API_KEYS = {"OPENAI_API_KEY": "foobar"}
    LM_LID = "gpt-3.5-turbo"
    EM_LID = "text-embedding-ada-002"
    API_PARAMS = {"openai_api_key": "foobar"}
    req = UpdateConfigRequest(
        model_provider_id=LM_GID, embeddings_provider_id=EM_GID, api_keys=API_KEYS
    )
    cm.update_config(req)
    return LM_GID, EM_GID, LM_LID, EM_LID, API_PARAMS


def test_snapshot_default_config(cm: ConfigManager, snapshot):
    config_from_cm: DescribeConfigResponse = cm.get_config()
    assert config_from_cm == snapshot(exclude=lambda prop, path: prop == "last_read")


def test_init_with_existing_config(cm: ConfigManager, common_cm_kwargs):
    configure_to_cohere(cm)
    del cm

    ConfigManager(**common_cm_kwargs)


def test_init_with_blocklists(cm: ConfigManager, common_cm_kwargs):
    configure_to_openai(cm)
    del cm

    blocked_providers = ["openai"]  # blocks EM
    blocked_models = ["openai-chat:gpt-3.5-turbo"]  # blocks LM
    kwargs = {
        **common_cm_kwargs,
        "blocked_providers": blocked_providers,
        "blocked_models": blocked_models,
    }
    test_cm = ConfigManager(**kwargs)
    assert test_cm._blocked_providers == blocked_providers
    assert test_cm._blocked_models == blocked_models
    assert test_cm.lm_gid == None
    assert test_cm.em_gid == None


def test_init_with_allowlists(cm: ConfigManager, common_cm_kwargs):
    configure_to_cohere(cm)
    del cm

    allowed_providers = ["openai"]  # blocks both LM & EM

    kwargs = {**common_cm_kwargs, "allowed_providers": allowed_providers}
    test_cm = ConfigManager(**kwargs)
    assert test_cm._allowed_providers == allowed_providers
    assert test_cm._allowed_models == None
    assert test_cm.lm_gid == None
    assert test_cm.em_gid == None


def test_init_with_default_values(
    cm_with_defaults: ConfigManager,
    config_path: str,
    schema_path: str,
    common_cm_kwargs,
):
    """
    Test that the ConfigManager initializes with the expected default values.

    Args:
        cm_with_defaults (ConfigManager): A ConfigManager instance with default values.
        config_path (str): The path to the configuration file.
        schema_path (str): The path to the schema file.
    """
    config_response = cm_with_defaults.get_config()
    # assert config response
    assert config_response.model_provider_id == "bedrock-chat:anthropic.claude-v1"
    assert (
        config_response.embeddings_provider_id == "bedrock:amazon.titan-embed-text-v1"
    )
    assert config_response.api_keys == ["OPENAI_API_KEY"]
    assert config_response.fields == {
        "bedrock-chat:anthropic.claude-v1": {
            "credentials_profile_name": "default",
            "region_name": "us-west-2",
        }
    }

    del cm_with_defaults

    log = logging.getLogger()
    lm_providers = get_lm_providers()
    em_providers = get_em_providers()
    kwargs = {
        **common_cm_kwargs,
        "defaults": {"model_provider_id": "bedrock-chat:anthropic.claude-v2"},
    }
    cm_with_defaults_override = ConfigManager(**kwargs)

    assert (
        cm_with_defaults_override.get_config().model_provider_id
        == "bedrock-chat:anthropic.claude-v1"
    )


def test_property_access_on_default_config(cm: ConfigManager):
    """Asserts that the CM behaves well with an empty, default
    configuration."""
    assert cm.lm_gid == None
    assert cm.em_gid == None
    assert cm.lm_provider == None
    assert cm.lm_provider_params == None
    assert cm.em_provider == None
    assert cm.em_provider_params == None


def test_indentation_depth(common_cm_kwargs, config_path):
    """Asserts that the CM indents the configuration and respects the
    `indentation_depth` trait when specified."""
    INDENT_DEPTH = 7
    ConfigManager(**common_cm_kwargs, indentation_depth=INDENT_DEPTH)
    with open(config_path) as f:
        config_file = f.read()
        config_lines = config_file.split("\n")
        lm_gid_line = next(
            line for line in config_lines if '"model_provider_id":' in line
        )
        assert lm_gid_line.startswith(" " * INDENT_DEPTH)
        assert not lm_gid_line.startswith(" " * (INDENT_DEPTH + 1))


def test_describe(cm: ConfigManager):
    LM_GID, EM_GID, LM_LID, EM_LID, API_PARAMS = configure_to_cohere(cm)

    config_desc = cm.get_config()
    assert config_desc.model_provider_id == LM_GID
    assert config_desc.embeddings_provider_id == EM_GID
    assert config_desc.api_keys == ["COHERE_API_KEY"]
    assert cm.lm_provider_params == {**API_PARAMS, "model_id": LM_LID}
    assert cm.em_provider_params == {**API_PARAMS, "model_id": EM_LID}


def test_update(cm: ConfigManager):
    LM_GID, EM_GID, LM_LID, EM_LID, API_PARAMS = configure_to_cohere(cm)

    new_config = cm.get_config()
    assert new_config.model_provider_id == LM_GID
    assert new_config.embeddings_provider_id == EM_GID
    assert new_config.api_keys == ["COHERE_API_KEY"]
    assert cm.lm_provider_params == {**API_PARAMS, "model_id": LM_LID}
    assert cm.em_provider_params == {**API_PARAMS, "model_id": EM_LID}


def test_update_no_empty_field_dicts(cm: ConfigManager, config_path):
    LM_GID, _, _, _, _ = configure_to_cohere(cm)
    cm.update_config(UpdateConfigRequest(fields={LM_GID: {}}))

    with open(config_path) as f:
        raw_config = json.loads(f.read())
        assert raw_config["fields"] == {}


def test_update_fails_with_invalid_req():
    with pytest.raises(ValidationError):
        UpdateConfigRequest(send_with_shift_enter=None)
    with pytest.raises(ValidationError):
        UpdateConfigRequest(fields=None)
    with pytest.raises(ValidationError):
        UpdateConfigRequest(api_keys=None)


def test_update_fails_without_auth(cm: ConfigManager):
    LM_GID = "cohere:xlarge"
    EM_GID = "cohere:large"
    req = UpdateConfigRequest(model_provider_id=LM_GID, embeddings_provider_id=EM_GID)
    with pytest.raises(AuthError):
        cm.update_config(req)


def test_update_after_describe(cm: ConfigManager):
    configure_to_cohere(cm)
    last_read = cm.get_config().last_read
    cm.update_config(
        UpdateConfigRequest(model_provider_id="cohere:medium", last_read=last_read)
    )

    new_config = cm.get_config()
    assert new_config.model_provider_id == "cohere:medium"


# TODO: make the test work on Linux including CI.
@pytest.mark.skip(reason="Flakey on Linux including CI.")
def test_forbid_write_write_conflict(cm: ConfigManager):
    configure_to_openai(cm)
    # call DescribeConfig
    last_read = cm.get_config().last_read

    # call UpdateConfig separately after DescribeConfig with `last_read` unset
    # to force a write
    cm.update_config(UpdateConfigRequest(model_provider_id="openai-chat:gpt-4"))

    # this update should fail, as this generates a write-write conflict (where
    # the second update clobbers the first update).
    with pytest.raises(WriteConflictError):
        cm.update_config(
            UpdateConfigRequest(
                model_provider_id="openai-chat:gpt-4-32k", last_read=last_read
            )
        )


def test_update_api_key(cm: ConfigManager):
    """Asserts that updates via direct edits to the config file are immediately
    reflected by the ConfigManager."""
    LM_GID, EM_GID, LM_LID, EM_LID, _ = configure_to_cohere(cm)
    cm.update_config(UpdateConfigRequest(api_keys={"COHERE_API_KEY": "barfoo"}))

    config_desc = cm.get_config()
    assert config_desc.api_keys == ["COHERE_API_KEY"]
    assert cm.lm_provider_params == {"cohere_api_key": "barfoo", "model_id": LM_LID}
    assert cm.em_provider_params == {"cohere_api_key": "barfoo", "model_id": EM_LID}


def test_delete_api_key(cm: ConfigManager):
    configure_to_cohere(cm)
    cm.update_config(UpdateConfigRequest(api_keys={"OPENAI_API_KEY": "asdf"}))
    assert cm.get_config().api_keys == ["COHERE_API_KEY", "OPENAI_API_KEY"]

    cm.delete_api_key("OPENAI_API_KEY")
    assert cm.get_config().api_keys == ["COHERE_API_KEY"]


def test_forbid_deleting_key_in_use(cm: ConfigManager):
    configure_to_cohere(cm)

    with pytest.raises(KeyInUseError):
        cm.delete_api_key("COHERE_API_KEY")


def test_handle_bad_provider_ids(cm_with_bad_provider_ids):
    config_desc = cm_with_bad_provider_ids.get_config()
    assert config_desc.model_provider_id is None
    assert config_desc.embeddings_provider_id is None
