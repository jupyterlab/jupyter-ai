"""Shared fixtures for the subpackage-docs aggregation integration tests.

These tests run a real ``sphinx-build`` against a synthesized filesystem
fixture: a minimal ``docs/source`` tree plus a sibling ``submodules/`` root
populated with fake subpackage docs. No real git submodules and no network are
involved. The layout mirrors the production repo so the ``subpackage_docs``
extension locates ``submodules/`` exactly as it does in the real build
(``<confdir>/../../submodules``)::

    <tmp>/
      docs/
        source/
          conf.py, index.md, contributors/index.md, developers/index.md, _ext/
      submodules/
        <repo>/docs/source/{contributors,developers}/...
        manifest.json
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

# docs/tests/ -> docs/ -> docs/source
_TESTS_DIR = Path(__file__).resolve().parent
_REAL_SOURCE = _TESTS_DIR.parent / "source"
_EXT_DIR = _REAL_SOURCE / "_ext"

# A minimal conf.py for the fixtures. It uses the real site theme (shibuya) so
# the tests exercise the actual sidebar-navigation rendering — a page-local
# toctree can render in the page body while still failing to appear in the
# global nav, so a body-only assertion (e.g. under the "basic" theme) would miss
# that regression.
_CONF_PY = """
import os
import sys

sys.path.insert(0, os.path.abspath("_ext"))

project = "Test Site"
extensions = ["myst_parser", "subpackage_docs"]
myst_enable_extensions = ["colon_fence"]
exclude_patterns = []
html_theme = "shibuya"
"""

# Root index tying the two aggregation pages into the doctree.
_ROOT_INDEX = """\
# Test Site

```{toctree}
:hidden:

contributors/index
developers/index
```
"""

_CONTRIB_INDEX = """\
# Contributor Guide

Top-level contributor guide.
"""

_DEV_INDEX = """\
# Developer Guide

Top-level developer guide.
"""


class Build:
    """The result of a Sphinx build: exit code + rendered HTML access."""

    def __init__(self, returncode: int, stdout: str, stderr: str, outdir: Path):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.outdir = outdir

    def html(self, docpath: str) -> str:
        """Return rendered HTML for a docname like 'contributors/index'."""
        return (self.outdir / f"{docpath}.html").read_text()

    def exists(self, docpath: str) -> bool:
        return (self.outdir / f"{docpath}.html").is_file()

    def nav_hrefs(self, docpath: str) -> list[str]:
        """Return the sidebar navigation (toctree) hrefs on a rendered page.

        These are the links the theme renders in its `toctree-l*` nav tree — i.e.
        what a reader can actually click to navigate, as opposed to links that
        merely appear in the page body or in `<head>` rel-links.
        """
        html = self.html(docpath)
        return re.findall(
            r'class="toctree-l\d[^"]*"[^>]*>\s*<a[^>]*href="([^"]+)"', html
        )


@pytest.fixture
def make_site(tmp_path: Path):
    """Return a builder that synthesizes a site + submodules and runs Sphinx.

    Usage::

        build = make_site(submodules={
            "my-repo": {"contributors": {"index.md": "# My Repo\\n..."}},
        })
        assert build.returncode == 0

    Each submodule spec maps ``repo-slug`` -> ``{section: {relpath: content}}``.
    A ``manifest.json`` is generated listing every provided repo (in the order
    given) so aggregation order is deterministic.
    """

    def _build(submodules: dict[str, dict[str, dict[str, str]]] | None = None) -> Build:
        submodules = submodules or {}

        root = tmp_path
        source = root / "docs" / "source"
        source.mkdir(parents=True)

        # Scaffold the minimal site.
        (source / "conf.py").write_text(_CONF_PY)
        (source / "index.md").write_text(_ROOT_INDEX)
        (source / "contributors").mkdir()
        (source / "contributors" / "index.md").write_text(_CONTRIB_INDEX)
        (source / "developers").mkdir()
        (source / "developers" / "index.md").write_text(_DEV_INDEX)

        # Symlink the real extension dir so the test exercises production code.
        (source / "_ext").symlink_to(_EXT_DIR)

        # Populate the submodules fixture root.
        subroot = root / "submodules"
        subroot.mkdir()
        manifest: dict[str, str] = {}
        for repo, sections in submodules.items():
            manifest[repo.replace("-", "_")] = f"fixture-org/{repo}"
            for section, files in sections.items():
                sdir = subroot / repo / "docs" / "source" / section
                sdir.mkdir(parents=True)
                for relpath, content in files.items():
                    target = sdir / relpath
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if isinstance(content, bytes):
                        target.write_bytes(content)
                    else:
                        target.write_text(content)
        (subroot / "manifest.json").write_text(json.dumps(manifest, indent=2))

        outdir = root / "build"
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "sphinx",
                "-b",
                "html",
                "-W",  # warnings become errors: the build must be clean
                "-q",
                str(source),
                str(outdir),
            ],
            capture_output=True,
            text=True,
        )
        return Build(proc.returncode, proc.stdout, proc.stderr, outdir)

    return _build
