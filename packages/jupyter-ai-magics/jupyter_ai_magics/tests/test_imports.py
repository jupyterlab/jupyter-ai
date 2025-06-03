import ast
import inspect
import sys

import jupyter_ai_magics


def test_uses_lazy_imports():
    assert "jupyter_ai_magics.exception" not in sys.modules
    jupyter_ai_magics.exception
    assert "jupyter_ai_magics.exception" in sys.modules


def test_all_includes_all_dynamic_imports():
    dynamic_imports = set(jupyter_ai_magics._modules_by_export.keys())
    assert dynamic_imports - set(jupyter_ai_magics.__all__) == set()


def test_dir_returns_all():
    assert set(jupyter_ai_magics.__all__) == set(dir(jupyter_ai_magics))


def test_all_type_checked():
    dynamic_imports = set(jupyter_ai_magics._modules_by_export.keys())
    tree = ast.parse(inspect.getsource(jupyter_ai_magics))
    imports_in_type_checking = {
        alias.asname if alias.asname else alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "TYPE_CHECKING"
        for stmt in node.body
        if isinstance(stmt, ast.ImportFrom)
        for alias in stmt.names
    }

    assert imports_in_type_checking == set(dynamic_imports)
