import json
import logging
import os

import pytest
from jupyter_ai.config_manager import (
    AuthError,
    ConfigManager,
    KeyInUseError,
    WriteConflictError,
)
from jupyter_ai.models import DescribeConfigResponse, UpdateConfigRequest
from jupyter_ai_magics.utils import get_em_providers, get_lm_providers
from pydantic import ValidationError


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
    }


@pytest.fixture
def cm(common_cm_kwargs):
    """The default ConfigManager instance, with an empty config and config schema."""
    return ConfigManager(**common_cm_kwargs)


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
    LM_GID = "openai-chat-new:gpt-3.5-turbo"
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


def test_init_with_existing_config(
    cm: ConfigManager, config_path: str, schema_path: str
):
    configure_to_cohere(cm)
    del cm

    log = logging.getLogger()
    lm_providers = get_lm_providers()
    em_providers = get_em_providers()
    ConfigManager(
        log=log,
        lm_providers=lm_providers,
        em_providers=em_providers,
        config_path=config_path,
        schema_path=schema_path,
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


def test_forbid_write_write_conflict(cm: ConfigManager):
    configure_to_openai(cm)
    # call DescribeConfig
    last_read = cm.get_config().last_read

    # call UpdateConfig separately after DescribeConfig with `last_read` unset
    # to force a write
    cm.update_config(UpdateConfigRequest(model_provider_id="openai-chat-new:gpt-4"))

    # this update should fail, as this generates a write-write conflict (where
    # the second update clobbers the first update).
    with pytest.raises(WriteConflictError):
        cm.update_config(
            UpdateConfigRequest(
                model_provider_id="openai-chat-new:gpt-4-32k", last_read=last_read
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
