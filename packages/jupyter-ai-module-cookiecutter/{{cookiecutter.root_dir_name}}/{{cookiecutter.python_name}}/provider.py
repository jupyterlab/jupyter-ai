from typing import ClassVar, List

from jupyter_ai import AuthStrategy, BaseProvider, Field

from .llm import TestLLM


class TestProvider(BaseProvider, TestLLM):
    """
    A test model provider implementation for developers to build from. A model
    provider inherits from 2 classes: 1) the `BaseProvider` class from
    `jupyter_ai`, and 2) an LLM class from `langchain`, i.e. a class inheriting
    from `LLM` or `BaseChatModel`.

    Any custom model first requires a `langchain` LLM class implementation.
    Please import one from `langchain`, or refer to the `langchain` docs for
    instructions on how to write your own. We offer an example in `./llm.py` for
    testing.

    To create a custom model provider from an existing `langchain`
    implementation, developers should edit this class' declaration to

    ```
    class TestModelProvider(BaseProvider, <langchain-llm-class>):
        ...
    ```

    Developers should fill in each of the below required class attributes.
    As the implementation is provided by the inherited LLM class, developers
    generally don't need to implement any methods. See the built-in
    implementations in `jupyter_ai_magics.providers.py` for further reference.

    The provider is made available to Jupyter AI by the entry point declared in
    `pyproject.toml`. If this class or parent module is renamed, make sure the
    update the entry point there as well.
    """

    id: ClassVar[str] = "test-provider"
    """ID for this provider class."""

    name: ClassVar[str] = "Test Provider"
    """User-facing name of this provider."""

    models: ClassVar[List[str]] = ["test-model-1"]
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
