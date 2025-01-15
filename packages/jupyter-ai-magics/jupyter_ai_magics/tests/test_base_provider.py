from typing import ClassVar, Optional

from pydantic import BaseModel

from ..providers import BaseProvider


def test_provider_classvars():
    """
    Asserts that class attributes are not omitted due to parent classes defining
    an instance field of the same name. This was a bug present in Pydantic v1,
    which led to an issue documented in #558.

    This bug is fixed as of `pydantic==2.10.2`, but we will keep this test in
    case this behavior changes in future releases.
    """

    class Parent(BaseModel):
        test: Optional[str] = None

    class Base(BaseModel):
        test: ClassVar[str]

    class Child(Base, Parent):
        test: ClassVar[str] = "expected"

    assert Child.test == "expected"
