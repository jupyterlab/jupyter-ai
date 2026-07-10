#!/usr/bin/env python3
"""Resolve the pin target for each documentation submodule.

Given the submodule manifest and jupyter-ai's ``pyproject.toml``, this script
decides which git ref every submodule should be pinned to, following pip /
PEP 440 semantics.

For each ``"pypi_name": "org/repo"`` entry in the manifest:

* The submodule path is ``submodules/<repo>`` (the part after the ``/``).
* The version range is looked up from ``pyproject.toml`` by ``pypi_name``,
  searching both ``[project].dependencies`` and every
  ``[project.optional-dependencies]`` group (so the ``magics`` / ``jupyternaut``
  extras are covered).
* The repo's tags are listed with ``git ls-remote`` over anonymous HTTPS.
  Tags are uniformly ``v``-prefixed PEP 440 versions; the ``v`` is stripped
  before parsing and non-PEP-440 tags are ignored.
* ``SpecifierSet(range).filter(versions)`` selects the candidates (this is the
  library pip itself uses, so pre-release handling matches pip exactly), and
  the maximum is the winner.
* If no tag matches (e.g. the package has not cut a matching release yet), the
  submodule is pinned to its default-branch HEAD and a warning is emitted.

Output: one tab-separated row per submodule on stdout::

    submodules/<repo>\t<https-url>\t<ref>\t<tag|branch>

All human-readable progress and warnings go to stderr so stdout stays a clean,
machine-parseable plan for the calling shell script.
"""

from __future__ import annotations

import json
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


def load_ranges(pyproject_path: str) -> dict[str, str]:
    """Map normalized package name -> version specifier string.

    Names are normalized to lowercase with ``-``/``_`` unified so manifest keys
    (which use ``_``) match pyproject entries (which may use either).
    """
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

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


def _norm(name: str) -> str:
    return name.strip().lower().replace("-", "_")


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


def resolve_tag(spec_string: str, tags: list[str]) -> str | None:
    """Return the winning tag name for a spec, or None if nothing matches."""
    spec = SpecifierSet(spec_string)
    # Map parsed Version -> original (v-prefixed) tag name.
    by_version: dict[Version, str] = {}
    for tag in tags:
        try:
            version = Version(tag.lstrip("v"))
        except InvalidVersion:
            continue
        # Keep the tag whose spelling matches this version.
        by_version[version] = tag
    matching = list(spec.filter(by_version.keys()))
    if not matching:
        return None
    return by_version[max(matching)]


def main() -> int:
    if len(sys.argv) != 3:
        log("usage: _resolve_doc_submodules.py <manifest.json> <pyproject.toml>")
        return 2
    manifest_path, pyproject_path = sys.argv[1], sys.argv[2]

    with open(manifest_path) as f:
        manifest = json.load(f)
    ranges = load_ranges(pyproject_path)

    rows: list[str] = []
    for pypi_name, org_repo in manifest.items():
        repo = org_repo.split("/", 1)[1]
        path = f"submodules/{repo}"
        url = f"https://github.com/{org_repo}.git"

        spec_string = ranges.get(_norm(pypi_name))
        if spec_string is None:
            log(
                f"warning: {pypi_name} is in the manifest but not a dependency "
                f"in {pyproject_path}; skipping"
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
