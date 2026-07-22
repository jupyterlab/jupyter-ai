"""Unit tests for the shared version/tag resolution helpers.

These cover the pure logic in ``_submodule_versions.py`` (floor extraction,
range/floor -> tag resolution, pyproject parsing) and the release-notes page
assembly in ``generate_release_notes.py`` that doesn't hit the network
(toctree insertion, previous-release-tag selection). No git or GitHub calls.

Run with: ``pytest scripts/test_submodule_versions.py``.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _submodule_versions as sv  # noqa: E402
import generate_release_notes as gen  # noqa: E402

PYPROJECT = """
[project]
name = "jupyter_ai"
dependencies = [
  "jupyterlab_chat>=0.23.0a3,<0.24.0",
  "jupyter_ai_router>=0.0.5,<0.1.0",
]

[project.optional-dependencies]
magics = ["jupyter_ai_litellm>=0.0.2,<0.1.0"]
jupyternaut = ["jupyter_ai_jupyternaut>=0.0.11,<0.1.0"]
"""


def test_norm_unifies_separators_and_case():
    assert sv._norm("Jupyter-AI_Router") == "jupyter_ai_router"


def test_spec_floor_reads_lower_bound():
    assert sv.spec_floor(">=0.1.0b1,<0.3.0") == "0.1.0b1"
    assert sv.spec_floor(">=0.0.8") == "0.0.8"
    assert sv.spec_floor("==1.2.3") == "1.2.3"


def test_spec_floor_none_without_lower_bound():
    assert sv.spec_floor("<0.3.0") is None
    assert sv.spec_floor("") is None


def test_load_floors_covers_deps_and_extras():
    floors = sv.load_floors_from_text(PYPROJECT)
    assert floors["jupyterlab_chat"] == "0.23.0a3"
    assert floors["jupyter_ai_router"] == "0.0.5"
    # extras are included
    assert floors["jupyter_ai_litellm"] == "0.0.2"
    assert floors["jupyter_ai_jupyternaut"] == "0.0.11"


def test_load_ranges_normalizes_names():
    ranges = sv.load_ranges_from_text(PYPROJECT)
    # SpecifierSet re-orders clauses, so compare the set of clauses.
    assert set(ranges["jupyter_ai_router"].split(",")) == {">=0.0.5", "<0.1.0"}


def test_resolve_tag_picks_max_matching():
    tags = ["v0.0.8", "v0.1.0b0", "v0.1.0b1", "v0.2.0"]
    # Range excludes 0.2.0; newest matching pre-release wins.
    assert sv.resolve_tag(">=0.1.0b1,<0.2.0", tags) == "v0.1.0b1"


def test_resolve_tag_none_when_no_match():
    assert sv.resolve_tag(">=9.0.0", ["v0.0.8", "v0.1.0"]) is None


def test_resolve_floor_tag_exact_and_spelling_tolerant():
    tags = ["v0.0.8", "v0.1.0b1", "v0.1.0beta0"]
    assert sv.resolve_floor_tag("0.1.0b1", tags) == "v0.1.0b1"
    # 0.1.0beta0 parses to the same Version as 0.1.0b0.
    assert sv.resolve_floor_tag("0.1.0b0", tags) == "v0.1.0beta0"


def test_resolve_floor_tag_none_when_absent():
    assert sv.resolve_floor_tag("9.9.9", ["v0.0.8"]) is None


# --- generate_release_notes pure logic ---


def test_normalize_version_adds_v_prefix():
    assert gen.normalize_version("3.1.0") == "v3.1.0"
    assert gen.normalize_version("v3.1.0") == "v3.1.0"
    assert gen.normalize_version("  3.0.4 ") == "v3.0.4"


def test_update_index_toctree_inserts_sorted_descending(tmp_path):
    index = tmp_path / "index.md"
    index.write_text(
        "# Releases\n\n```{toctree}\n:maxdepth: 1\n```\n",
        encoding="utf-8",
    )
    gen.update_index_toctree(str(index), "v3.0.1")
    gen.update_index_toctree(str(index), "v3.1.0")
    gen.update_index_toctree(str(index), "v3.0.4")
    text = index.read_text(encoding="utf-8")
    # Newest first.
    lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("v")]
    assert lines == ["v3.1.0", "v3.0.4", "v3.0.1"]


def test_update_index_toctree_is_idempotent(tmp_path):
    index = tmp_path / "index.md"
    index.write_text(
        "# Releases\n\n```{toctree}\n:maxdepth: 1\nv3.1.0\n```\n",
        encoding="utf-8",
    )
    gen.update_index_toctree(str(index), "v3.1.0")
    text = index.read_text(encoding="utf-8")
    assert text.count("v3.1.0") == 1


def test_update_index_toctree_preserves_options(tmp_path):
    index = tmp_path / "index.md"
    index.write_text(
        "# Releases\n\n```{toctree}\n:maxdepth: 1\n```\n",
        encoding="utf-8",
    )
    gen.update_index_toctree(str(index), "v3.1.0")
    text = index.read_text(encoding="utf-8")
    assert ":maxdepth: 1" in text
    assert "```{toctree}" in text
