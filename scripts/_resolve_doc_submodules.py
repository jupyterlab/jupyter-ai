#!/usr/bin/env python3
"""Resolve the pin target for each documentation submodule.

Given the submodule manifest and jupyter-ai's ``pyproject.toml``, this script
decides which git ref every submodule should be pinned to. It has two modes,
matching how the docs are meant to move:

``main`` (default)
    Pin every submodule to its **default-branch HEAD**. This is what the routine
    "update submodule documentation" job uses so the ``latest`` docs (built from
    jupyter-ai's ``main``) always show each subpackage's newest, possibly
    unreleased docs — no release required.

``release``
    Pin each submodule to the latest git tag satisfying that package's version
    range in ``pyproject.toml``, following pip / PEP 440 semantics. This is what
    the release hook uses so a release tag captures a **coherent, frozen**
    snapshot of the subpackage docs that ship with that jupyter-ai version.

    * The version range is looked up by ``pypi_name`` across
      ``[project].dependencies`` and every ``[project.optional-dependencies]``
      group (so the ``magics`` / ``jupyternaut`` extras are covered).
    * Tags are listed with ``git ls-remote`` over anonymous HTTPS. They are
      uniformly ``v``-prefixed PEP 440 versions; the ``v`` is stripped before
      parsing and non-PEP-440 tags are ignored.
    * ``SpecifierSet(range).filter(versions)`` selects the candidates (the same
      library pip uses, so pre-release handling matches pip exactly); the max
      wins. If nothing matches, that submodule falls back to its default-branch
      HEAD with a warning.

For each ``"pypi_name": "org/repo"`` entry the submodule path is
``submodules/<repo>`` (the part after the ``/``).

Output: one tab-separated row per submodule on stdout::

    submodules/<repo>\t<https-url>\t<ref>\t<tag|branch>

All human-readable progress and warnings go to stderr so stdout stays a clean,
machine-parseable plan for the calling shell script.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Shared version/tag resolution, kept in one place so this tool and the
# release-notes generator can't drift on how a floor maps to a git tag.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _submodule_versions import (  # noqa: E402
    _norm,
    default_branch,
    list_tags,
    load_ranges,
    log,
    resolve_tag,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="path to submodules/manifest.json")
    parser.add_argument("pyproject", help="path to pyproject.toml")
    parser.add_argument(
        "--mode",
        choices=("main", "release"),
        default="main",
        help=(
            "main: pin every submodule to its default-branch HEAD (freshest "
            "docs, for the routine update job). release: pin to the latest tag "
            "matching each package's pyproject range (frozen snapshot, for the "
            "release hook). Default: main."
        ),
    )
    args = parser.parse_args()

    with open(args.manifest) as f:
        manifest = json.load(f)
    ranges = load_ranges(args.pyproject) if args.mode == "release" else {}

    rows: list[str] = []
    for pypi_name, org_repo in manifest.items():
        repo = org_repo.split("/", 1)[1]
        path = f"submodules/{repo}"
        url = f"https://github.com/{org_repo}.git"

        if args.mode == "main":
            branch = default_branch(url)
            log(f"  {pypi_name}: main -> {branch} HEAD")
            rows.append(f"{path}\t{url}\t{branch}\tbranch")
            continue

        # release mode: resolve the tag matching this package's version range.
        spec_string = ranges.get(_norm(pypi_name))
        if spec_string is None:
            log(
                f"warning: {pypi_name} is in the manifest but not a dependency "
                f"in {args.pyproject}; skipping"
            )
            continue

        tags = list_tags(url)
        tag = resolve_tag(spec_string, tags)
        if tag is not None:
            log(f"  {pypi_name}: {spec_string or '(any)'} -> {tag}")
            rows.append(f"{path}\t{url}\t{tag}\ttag")
        else:
            branch = default_branch(url)
            log(
                f"  {pypi_name}: {spec_string or '(any)'} matched no tag "
                f"(available: {', '.join(tags) or 'none'}); "
                f"pinning to default branch '{branch}' HEAD"
            )
            rows.append(f"{path}\t{url}\t{branch}\tbranch")

    print("\n".join(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
