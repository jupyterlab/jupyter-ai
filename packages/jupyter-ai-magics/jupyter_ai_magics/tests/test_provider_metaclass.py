from typing import ClassVar, Optional

from langchain.pydantic_v1 import BaseModel

from ..providers import ProviderMetaclass


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
