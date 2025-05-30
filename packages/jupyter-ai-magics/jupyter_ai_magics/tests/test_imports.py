import sys

import jupyter_ai_magics


def test_uses_lazy_imports():
    assert "jupyter_ai_magics.exception" not in sys.modules
    jupyter_ai_magics.exception
    assert "jupyter_ai_magics.exception" in sys.modules


def test_all_includes_all_dynamic_imports():
    dynamic_imports = set(jupyter_ai_magics._dynamic_imports_map.keys())
    assert dynamic_imports - set(jupyter_ai_magics.__all__) == set()


def test_dir_returns_all():
    assert set(jupyter_ai_magics.__all__) == set(dir(jupyter_ai_magics))
