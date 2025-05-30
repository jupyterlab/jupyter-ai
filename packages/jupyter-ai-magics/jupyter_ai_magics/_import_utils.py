"""
MIT License

Copyright (c) LangChain, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from importlib import import_module
from typing import Union


def import_attr(
    attr_name: str,
    module_name: Union[str, None],
    package: Union[str, None],
) -> object:
    """Import an attribute from a module located in a package.

    This utility function is used in custom __getattr__ methods within __init__.py
    files to dynamically import attributes.

    Args:
        attr_name: The name of the attribute to import.
        module_name: The name of the module to import from. If None, the attribute
            is imported from the package itself.
        package: The name of the package where the module is located.
    """
    if module_name == "__module__" or module_name is None:
        try:
            result = import_module(f".{attr_name}", package=package)
        except ModuleNotFoundError:
            msg = f"module '{package!r}' has no attribute {attr_name!r}"
            raise AttributeError(msg) from None
    else:
        try:
            module = import_module(f".{module_name}", package=package)
        except ModuleNotFoundError:
            msg = f"module '{package!r}.{module_name!r}' not found"
            raise ImportError(msg) from None
        result = getattr(module, attr_name)
    return result
