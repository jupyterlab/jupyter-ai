import pandas as pd
import inspect
import random
import types
from typing import Any, Callable
import io
from pydantic.v1 import BaseModel

class VariableDescription(BaseModel):
    name: str
    type: str
    value: str
    # We cant use schema as it is an attribute of pydantic
    structure: str | None = None

    def format(self) -> str:
        res = "<variable>\n"
        res += f"<name>{self.name}</name>\n"
        res += f"<type>{self.type}</type>\n"
        if self.structure:
            res += f"<schema>{self.structure}</schema>\n"
        res += f"<value>{self.value}</value>\n"
        res += "</variable>\n"

        return res


def default_handler(name: str, x: Any):
    fqn = f"{x.__class__.__module__}.{x.__class__.__name__}"
    return VariableDescription(
        name=name,
        type=fqn,
        value=str(x)
    )

def dataframe_handler(name: str, x: pd.DataFrame):
    info_buf = io.StringIO()
    x.info(buf=info_buf, memory_usage=False, show_counts=False)

    return VariableDescription(
        name=name,
        type="pandas.DataFrame",
        value="Some random rows from the dataframe:\n" + str(x.sample(min(5, len(x)))),
        structure=info_buf.getvalue()
    )

def function_handler(name: str, x: Callable):
    return VariableDescription(
        name=name,
        type="function",
        value=inspect.getsource(x)
    )

def basic_type_handler(name: str, x: Any):
    return VariableDescription(
        name=name,
        type=type(x).__name__,
        value=x
    )

def list_handler(name: str, x: Any):
    return VariableDescription(
        name=name,
        type=type(x).__name__,
        value=str(random.sample(list(x), 5)),
        structure=f"Size: {len(x)}"
    )

def string_handler(name: str, x: Any):
    val = x if len(x) < 10 else x[:10] + "..."
    return basic_type_handler(name, val)


class DescriberRegistry:
    """
    Maintains a registry of handlers for different dtypes for sending context
    to an LLM in jupyter ai

    This also accespts a _repr_llm_ that should return a dict with mapping of mime type to content.
    Currently only application/jupyer+ai+var is supported.

    Sample Usage:
    >>> from jupyter_ai._variable_describer import DescriberRegistry, VariableDescription
    >>> int_handler = lambda name, value: VariableDescription(name=name, type="int", value=value)
    >>> DescriberRegistry.register(int, int_handler)
    """
    registry: dict[type, Callable[[str, Any], str]] = {}

    @classmethod
    def _init(cls):
        cls.register(pd.DataFrame, dataframe_handler)
        cls.register(types.FunctionType, function_handler)
        cls.register(int, basic_type_handler)
        cls.register(float, basic_type_handler)
        cls.register(str, string_handler)
        cls.register(list, list_handler)
        cls.register(tuple, list_handler)
        cls.register(set, list_handler)

    @classmethod
    def register(cls, var_type: type, handler: Callable[[str, Any], str]):
        cls.registry[var_type] = handler

    @classmethod
    def get(cls, value: Any):
        return cls.registry.get(type(value), None)

    @classmethod
    def _get_repr_handler(cls):
        def _repr_handler(name: str, value: Any):
            repr_llm = value._repr_llm_(name=name)
            description = repr_llm.get("application/jupyer+ai+var", None)

            if description is None:
                return default_handler(name, value)

            return VariableDescription.parse_obj(description)
        return _repr_handler


    @classmethod
    def describe(cls, name: str, value: Any) -> str:
        """
        Returns a description of the variable in an XML format
        """
        # Priority to set handlers
        # followed by repr_llm handlers
        # followed by default handlers
        handler = cls.get(value)

        if handler is not None and hasattr(value, "_repr_llm_"):
            handler = cls._get_repr_handler()

        if handler is None:
            handler = default_handler

        desc = handler(name, value)
        if not isinstance(desc, VariableDescription):
            raise TypeError("Handler must return an instance of VariableDescription")

        return desc.format()

DescriberRegistry._init()

def describe_var(name: str, value: Any) -> str:
    return DescriberRegistry.describe(name, value)