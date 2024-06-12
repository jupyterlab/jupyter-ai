from types import MappingProxyType
from typing import ClassVar, Optional

from langchain.pydantic_v1 import BaseModel
from pytest import raises

from ..providers import BaseProvider, ProviderMetaclass


def test_provider_metaclass():
    """
    Asserts that the metaclass prevents class attributes from being omitted due
    to parent classes defining an instance field of the same name.

    You can reproduce the original issue by removing the
    `metaclass=ProviderMetaclass` argument from the definition of `Child`.
    """

    class Parent(BaseModel):
        test: Optional[str]

    class Base(BaseModel):
        test: ClassVar[str]

    class Child(Base, Parent, metaclass=ProviderMetaclass):
        test: ClassVar[str] = "expected"

    assert Child.test == "expected"


def test_base_provider_server_settings_read_only():
    BaseProvider.server_settings = MappingProxyType({})

    with raises(AttributeError, match="'server_settings' attribute was already set"):
        BaseProvider.server_settings = MappingProxyType({})
