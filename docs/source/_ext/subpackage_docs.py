"""Sphinx extension: aggregate subpackage docs into the Jupyter AI site.

Jupyter AI is composed of many subpackages under the ``jupyter-ai-contrib``
GitHub org. Each subpackage may ship its own **contributor** and **developer**
docs inside its repo, under ``docs/source/{contributors,developers}/``. Those
repos are vendored into the main ``jupyter-ai`` repo as git submodules
(sparse-checked-out to ``docs/`` only) under ``submodules/<repo>/``, registered
in ``submodules/manifest.json``.

This extension pulls each subpackage's contributor/developer docs into the
Sphinx build as versioned subpages::

    submodules/<repo>/docs/source/contributors/  ->  contributors/<repo>/
    submodules/<repo>/docs/source/developers/    ->  developers/<repo>/

The full subtree is copied (so a subpackage may ship nested pages + images),
and each subpackage's own ``index`` H1 becomes its subpage title. A
``{toctree}`` entry is then injected into the matching aggregation page
(``contributors/index`` or ``developers/index``) so the subpage appears in that
section's sidebar navigation.

Rollout is gradual: most subpackages do not define these docs yet, so most
submodules contribute nothing and the build renders no new pages. A subpackage
with neither section — or a missing/empty ``docs/`` (e.g. a repo not yet checked
out, or one without a matching release tag) — is silently skipped, and the build
still succeeds.

The submodules root is located relative to ``conf.py`` (``app.confdir``):
``<confdir>/../../submodules``. Tests exercise this extension by building a
minimal ``docs/source`` tree with a sibling ``submodules/`` fixture root — no
environment flag is involved.

The generated ``contributors/<repo>/`` and ``developers/<repo>/`` staging dirs
are git-ignored (see ``docs/source/{contributors,developers}/.gitignore``);
build output is never committed.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.util import logging

logger = logging.getLogger(__name__)

# The two independent aggregation points. A subpackage may appear under one,
# both, or neither.
AGGREGATION_SECTIONS = ("contributors", "developers")


def _submodules_root(app: Sphinx) -> Path:
    """Return the ``submodules/`` root for this build.

    ``app.confdir`` is ``docs/source``; the submodules root is two levels up
    (``<repo>/submodules``).
    """
    return Path(app.confdir).parent.parent / "submodules"


def _manifest_repo_slugs(submodules_root: Path) -> list[str]:
    """Return submodule directory names, in manifest order.

    The manifest maps ``"pypi_name": "org/repo"``; the submodule path is
    ``submodules/<repo>``. If the manifest is absent, fall back to scanning the
    directories under the submodules root so a build still works without one.
    """
    manifest_path = submodules_root / "manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        return [org_repo.split("/", 1)[1] for org_repo in manifest.values()]
    if submodules_root.is_dir():
        return sorted(p.name for p in submodules_root.iterdir() if p.is_dir())
    return []


def _stage_subpackage_docs(app: Sphinx) -> None:
    """Copy each subpackage's contributor/developer docs into staging dirs.

    Runs on ``builder-inited``. For every submodule that ships
    ``docs/source/<section>/index.*``, copy the whole ``<section>`` subtree to
    ``<srcdir>/<section>/<repo>/``. Records what was staged on the build
    environment for the ``source-read`` hook to consume.
    """
    submodules_root = _submodules_root(app)
    srcdir = Path(app.srcdir)
    staged: dict[str, list[str]] = {section: [] for section in AGGREGATION_SECTIONS}

    for repo in _manifest_repo_slugs(submodules_root):
        for section in AGGREGATION_SECTIONS:
            src = submodules_root / repo / "docs" / "source" / section
            # Require an index page; a section dir without one has nothing to
            # anchor a toctree entry, so treat it as absent.
            if not (src.is_dir() and any(src.glob("index.*"))):
                continue
            dest = srcdir / section / repo
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            staged[section].append(repo)
            logger.info("[subpackage-docs] staged %s docs for '%s'", section, repo)

    # Stash on the app so the source-read hook (and tests) can read it back.
    app._subpackage_docs_staged = staged  # type: ignore[attr-defined]


def _inject_subpackage_toctrees(app: Sphinx, docname: str, source: list[str]) -> None:
    """Append a toctree of staged subpages to each aggregation index.

    Runs on ``source-read``. When Sphinx reads ``contributors/index`` or
    ``developers/index``, append a ``{toctree}`` listing the subpages staged for
    that section. Each subpackage's own ``index`` H1 supplies the nav title. The
    toctree is not ``:hidden:`` so the subpackages surface both in the section's
    sidebar navigation and as a "Subpackages" list on the index page itself.
    """
    staged = getattr(app, "_subpackage_docs_staged", {})
    for section in AGGREGATION_SECTIONS:
        if docname != f"{section}/index":
            continue
        repos = staged.get(section, [])
        if not repos:
            return
        entries = "\n".join(f"{repo}/index" for repo in repos)
        source[0] += (
            "\n\n```{toctree}\n:caption: Subpackages\n:maxdepth: 1\n\n"
            f"{entries}\n```\n"
        )


def setup(app: Sphinx) -> dict:
    app.connect("builder-inited", _stage_subpackage_docs)
    app.connect("source-read", _inject_subpackage_toctrees)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
