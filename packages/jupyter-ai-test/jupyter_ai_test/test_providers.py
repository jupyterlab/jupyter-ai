from typing import ClassVar, List

from jupyter_ai import AuthStrategy, BaseProvider, Field

from .test_llms import TestLLM, TestLLMWithStreaming


class TestProvider(BaseProvider, TestLLM):
    id: ClassVar[str] = "test-provider"
    """ID for this provider class."""

    name: ClassVar[str] = "Test Provider"
    """User-facing name of this provider."""

    models: ClassVar[List[str]] = ["test"]
    """List of supported models by their IDs. For registry providers, this will
    be just ["*"]."""

    help: ClassVar[str] = None
    """Text to display in lieu of a model list for a registry provider that does
    not provide a list of models."""

    model_id_key: ClassVar[str] = "model_id"
    """Kwarg expected by the upstream LangChain provider."""

    model_id_label: ClassVar[str] = "Model ID"
    """Human-readable label of the model ID."""

    pypi_package_deps: ClassVar[List[str]] = []
    """List of PyPi package dependencies."""

    auth_strategy: ClassVar[AuthStrategy] = None
    """Authentication/authorization strategy. Declares what credentials are
    required to use this model provider. Generally should not be `None`."""

    registry: ClassVar[bool] = False
    """Whether this provider is a registry provider."""

    fields: ClassVar[List[Field]] = []
    """User inputs expected by this provider when initializing it. Each `Field` `f`
    should be passed in the constructor as a keyword argument, keyed by `f.key`."""


class TestProviderWithStreaming(BaseProvider, TestLLMWithStreaming):
    id: ClassVar[str] = "test-provider-with-streaming"
    """ID for this provider class."""

    name: ClassVar[str] = "Test Provider (streaming)"
    """User-facing name of this provider."""

    models: ClassVar[List[str]] = ["test"]
    """List of supported models by their IDs. For registry providers, this will
    be just ["*"]."""

    help: ClassVar[str] = None
    """Text to display in lieu of a model list for a registry provider that does
    not provide a list of models."""

    model_id_key: ClassVar[str] = "model_id"
    """Kwarg expected by the upstream LangChain provider."""

    model_id_label: ClassVar[str] = "Model ID"
    """Human-readable label of the model ID."""

    pypi_package_deps: ClassVar[List[str]] = []
    """List of PyPi package dependencies."""

    auth_strategy: ClassVar[AuthStrategy] = None
    """Authentication/authorization strategy. Declares what credentials are
    required to use this model provider. Generally should not be `None`."""

    registry: ClassVar[bool] = False
    """Whether this provider is a registry provider."""

    fields: ClassVar[List[Field]] = []
    """User inputs expected by this provider when initializing it. Each `Field` `f`
    should be passed in the constructor as a keyword argument, keyed by `f.key`."""


class TestProviderAskLearnUnsupported(BaseProvider, TestLLMWithStreaming):
    id: ClassVar[str] = "test-provider-ask-learn-unsupported"
    """ID for this provider class."""

    name: ClassVar[str] = "Test Provider (/learn and /ask unsupported)"
    """User-facing name of this provider."""

    models: ClassVar[List[str]] = ["test"]
    """List of supported models by their IDs. For registry providers, this will
    be just ["*"]."""

    help: ClassVar[str] = None
    """Text to display in lieu of a model list for a registry provider that does
    not provide a list of models."""

    model_id_key: ClassVar[str] = "model_id"
    """Kwarg expected by the upstream LangChain provider."""

    model_id_label: ClassVar[str] = "Model ID"
    """Human-readable label of the model ID."""

    pypi_package_deps: ClassVar[List[str]] = []
    """List of PyPi package dependencies."""

    auth_strategy: ClassVar[AuthStrategy] = None
    """Authentication/authorization strategy. Declares what credentials are
    required to use this model provider. Generally should not be `None`."""

    registry: ClassVar[bool] = False
    """Whether this provider is a registry provider."""

    fields: ClassVar[List[Field]] = []
    """User inputs expected by this provider when initializing it. Each `Field` `f`
    should be passed in the constructor as a keyword argument, keyed by `f.key`."""

    unsupported_slash_commands = {"/learn", "/ask"}
