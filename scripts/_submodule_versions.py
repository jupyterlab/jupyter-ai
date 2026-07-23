#!/usr/bin/env python3
"""Shared version/tag resolution for the documentation submodules.

Both the docs-submodule pinning tooling (``_resolve_doc_submodules.py`` /
``update-doc-submodules.sh``) and the release-notes generator
(``generate_release_notes.py``) need to answer the same questions about a
subpackage:

* What version range / floor does ``jupyter-ai``'s ``pyproject.toml`` declare
  for it? (``load_ranges`` / ``load_floors``)
* Which ``v``-prefixed git tags does its repo publish? (``list_tags``)
* Which tag satisfies a range, or exactly matches a floor? (``resolve_tag`` /
  ``resolve_floor_tag``)
* What is its default branch? (``default_branch``)

Factoring these here keeps the two tools from drifting on how a package's
floor maps to a git tag — the single fact both depend on.

Tag conventions (uniform across the ``jupyter-ai-contrib`` subpackages):
tags are ``v``-prefixed PEP 440 versions; the ``v`` is stripped before parsing
and non-PEP-440 tags are ignored. ``git ls-remote`` is used over anonymous
HTTPS, so no checkout or auth is required.
"""

from __future__ import annotations

import subprocess
import sys

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.10 and earlier
    import tomli as tomllib  # type: ignore[no-redef]


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def _norm(name: str) -> str:
    """Normalize a package name for cross-source matching.

    Manifest keys use ``_``; pyproject entries may use either ``-`` or ``_``.
    Lowercase and unify both to ``_`` so they compare equal.
    """
    return name.strip().lower().replace("-", "_")


def load_ranges_from_text(pyproject_text: str) -> dict[str, str]:
    """Map normalized package name -> version specifier string, from TOML text.

    Reads ``[project].dependencies`` plus every
    ``[project.optional-dependencies]`` group (so the ``magics`` / ``jupyternaut``
    extras are covered). Accepting text (not just a path) lets callers resolve
    ranges from ``git show <tag>:pyproject.toml`` without a checkout.
    """
    data = tomllib.loads(pyproject_text)

    project = data.get("project", {})
    req_strings: list[str] = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        req_strings.extend(group)

    ranges: dict[str, str] = {}
    for req_string in req_strings:
        try:
            req = Requirement(req_string)
        except Exception:  # pragma: no cover - defensive
            continue
        ranges[_norm(req.name)] = str(req.specifier)
    return ranges


def load_ranges(pyproject_path: str) -> dict[str, str]:
    """Map normalized package name -> version specifier string, from a file."""
    with open(pyproject_path, encoding="utf-8") as f:
        return load_ranges_from_text(f.read())


def spec_floor(spec_string: str) -> str | None:
    """Return the ``>=`` lower bound of a specifier string, or None.

    The doc submodule windows are defined by each dependency's minimum
    *floor* — the ``>=X`` bound — not its ceiling or latest tag. A specifier
    like ``>=0.1.0b1,<0.3.0`` yields ``0.1.0b1``. Any of ``>=`` / ``==`` / ``~=``
    counts as a floor; the largest such bound wins if several are present.
    """
    floors: list[Version] = []
    for spec in SpecifierSet(spec_string):
        if spec.operator in (">=", "==", "~=", "==="):
            try:
                floors.append(Version(spec.version))
            except InvalidVersion:
                continue
    if not floors:
        return None
    return str(max(floors))


def load_floors_from_text(pyproject_text: str) -> dict[str, str]:
    """Map normalized package name -> floor version string, from TOML text."""
    floors: dict[str, str] = {}
    for name, spec_string in load_ranges_from_text(pyproject_text).items():
        floor = spec_floor(spec_string)
        if floor is not None:
            floors[name] = floor
    return floors


def optional_only_names(pyproject_text: str) -> set[str]:
    """Return the normalized names of packages that are optional-only.

    A package is "optional" if it appears in ``[project.optional-dependencies]``
    but NOT in the core ``[project.dependencies]`` — i.e. installing jupyter-ai
    without extras does not pull it in. A package listed in both is effectively
    required, so it is not reported as optional.
    """
    data = tomllib.loads(pyproject_text)
    project = data.get("project", {})

    core: set[str] = set()
    for req_string in project.get("dependencies", []):
        try:
            core.add(_norm(Requirement(req_string).name))
        except Exception:  # pragma: no cover - defensive
            continue

    optional: set[str] = set()
    for group in project.get("optional-dependencies", {}).values():
        for req_string in group:
            try:
                optional.add(_norm(Requirement(req_string).name))
            except Exception:  # pragma: no cover - defensive
                continue

    return optional - core


def list_tags(url: str) -> list[str]:
    """Return the repo's tag names (``refs/tags/*``, deref peels stripped)."""
    out = subprocess.run(
        ["git", "ls-remote", "--tags", "--refs", url],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    tags = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[1].startswith("refs/tags/"):
            tags.append(parts[1][len("refs/tags/") :])
    return tags


def default_branch(url: str) -> str:
    """Return the remote's default branch name (from its HEAD symref)."""
    out = subprocess.run(
        ["git", "ls-remote", "--symref", url, "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    for line in out.splitlines():
        # e.g. "ref: refs/heads/main\tHEAD"
        if line.startswith("ref:"):
            ref = line[len("ref:") :].strip().split("\t")[0].strip()
            if ref.startswith("refs/heads/"):
                return ref[len("refs/heads/") :]
    return "main"


def _tags_by_version(tags: list[str]) -> dict[Version, str]:
    """Map parsed Version -> original (v-prefixed) tag name."""
    by_version: dict[Version, str] = {}
    for tag in tags:
        try:
            version = Version(tag.lstrip("v"))
        except InvalidVersion:
            continue
        by_version[version] = tag
    return by_version


def resolve_tag(spec_string: str, tags: list[str]) -> str | None:
    """Return the winning tag name for a spec, or None if nothing matches.

    Uses ``SpecifierSet.filter`` (the same selection pip uses, so pre-release
    handling matches pip exactly); the maximum matching version wins.
    """
    spec = SpecifierSet(spec_string)
    by_version = _tags_by_version(tags)
    matching = list(spec.filter(by_version.keys()))
    if not matching:
        return None
    return by_version[max(matching)]


def resolve_floor_tag(floor_version: str, tags: list[str]) -> str | None:
    """Return the tag whose version equals ``floor_version``, or None.

    A floor maps to the ``v``-prefixed tag of that exact version (e.g. floor
    ``0.1.0b1`` -> tag ``v0.1.0b1``). Matching by parsed ``Version`` (rather than
    string) tolerates spelling differences like ``0.1.0beta1`` vs ``0.1.0b1``.
    """
    try:
        target = Version(floor_version.lstrip("v"))
    except InvalidVersion:
        return None
    return _tags_by_version(tags).get(target)
