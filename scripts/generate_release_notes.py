#!/usr/bin/env python3
"""Generate a docs release-notes page for a new jupyter-ai version.

The docs "Releases" section is the source of truth for jupyter-ai release notes
— not Jupyter Releaser's changelog and not GitHub releases. This script builds
one per-version page (``docs/source/releases/<version>.md``) that aggregates,
for every documentation submodule, the PRs and contributors that landed in the
window between the *previous* release's floor and *this* release's floor for
that submodule.

Why floors, per submodule
-------------------------
``jupyter-ai``'s ``pyproject.toml`` declares a minimum version *floor*
(``>=X``) for each subpackage. Bumping a floor between releases is exactly what
"ships new subpackage code in this jupyter-ai release" means, so the release
notes for a subpackage are the PRs between its floor at the previous release and
its floor at this release:

* new ``v3.1.0`` and previous release ``v3.0.1`` ⇒ for each submodule include
  the PRs between its floor at ``v3.0.1`` and its floor at ``v3.1.0``.

"Previous release" is the latest **official** (non-prerelease) ``v``-tag that is
reachable on the target branch and lower than ``version`` — so a ``3.1.0`` cut
from ``main`` diffs against the last stable on ``main`` (e.g. ``v3.0.1``), never
a ``3.0.x`` patch that only exists on a maintenance branch.

Each floor maps to that subpackage's ``v``-prefixed git tag. The window handed
to Jupyter Releaser's own ``get_version_entry`` starts at the *merge-base* of the
two floor tags (see ``window_start``) — not the raw previous-floor tag — so a
subpackage patch cut from a maintenance branch doesn't skew the date boundary and
drop PRs that shipped on the main line. In the common in-line case the merge-base
*is* the previous-floor tag. Reusing ``get_version_entry`` means grouping-by-label
and the contributors list match the releaser exactly — no hand-rolled variant.

The new version's floors are read from the **working-tree** ``pyproject.toml``
(Step 0 runs before the release is tagged, once the floors have been bumped);
the previous version's floors are read from ``git show <prev_tag>:pyproject.toml``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

import requests  # github_activity depends on requests; always available here
from packaging.version import InvalidVersion, Version

# Shared version/tag resolution (see _submodule_versions.py) — the single
# definition of how a package floor maps to a git tag, shared with the
# docs-submodule pinning tooling so the two can't drift.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _submodule_versions import (  # noqa: E402
    _norm,
    default_branch,
    list_tags,
    load_floors_from_text,
    log,
    resolve_floor_tag,
)

# Jupyter Releaser's changelog builder — reused wholesale for PR aggregation.
from jupyter_releaser import changelog  # noqa: E402


def normalize_version(version: str) -> str:
    """Return ``version`` with a leading ``v`` (e.g. ``3.1.0`` -> ``v3.1.0``)."""
    version = version.strip()
    return version if version.startswith("v") else f"v{version}"


def git(repo_root: str, *args: str) -> str:
    """Run a git command in ``repo_root`` and return stripped stdout."""
    return subprocess.run(
        ["git", "-C", repo_root, *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def previous_release_tag(repo_root: str, version: str, branch: str) -> str | None:
    """Return the latest official release tag before ``version`` on ``branch``.

    "Official" = non-prerelease ``v``-prefixed PEP 440 tag. Only tags reachable
    on ``branch`` (``git tag --merged``) count, so a release cut from ``main``
    diffs against the last stable that actually shipped on ``main`` — not a
    patch that lives only on a maintenance branch.
    """
    target = Version(version.lstrip("v"))

    # `git tag --merged <branch>` lists tags reachable from that branch. Fall
    # back to the plain tag list if the branch ref isn't available locally.
    try:
        raw = git(repo_root, "tag", "--merged", branch)
    except subprocess.CalledProcessError:
        raw = git(repo_root, "tag")

    candidates: list[tuple[Version, str]] = []
    for tag in raw.splitlines():
        tag = tag.strip()
        if not tag.startswith("v"):
            continue
        try:
            parsed = Version(tag.lstrip("v"))
        except InvalidVersion:
            continue
        if parsed.is_prerelease:
            continue
        if parsed < target:
            candidates.append((parsed, tag))

    if not candidates:
        return None
    return max(candidates, key=lambda pv: pv[0])[1]


def show_file_at(repo_root: str, ref: str, path: str) -> str:
    """Return the contents of ``path`` as of git ``ref``."""
    return git(repo_root, "show", f"{ref}:{path}")


def window_start(org_repo: str, prev_tag: str, new_tag: str, auth: str | None) -> str:
    """Return the ref to start a submodule's PR window at: the merge-base.

    A subpackage's previous floor and new floor don't always sit on one line.
    A patch (e.g. ``v0.2.6``) is cut from a maintenance branch *after* ``main``
    has moved on, so ``v0.2.6`` can be dated later than PRs that shipped in
    ``v0.3.0`` on ``main``. Since github_activity filters PRs by the *date* of
    the ``since`` ref, starting at the raw previous-floor tag would skip that
    intervening batch.

    The correct start is where the two floors last shared history — their
    merge-base. When a fix is backported, it exists on both branches, so the
    merge-base excludes the shared past and keeps exactly the new commits on the
    release line. GitHub's compare API returns this as ``merge_base_commit``;
    ``base_commit`` is ``prev_tag``'s own commit. When they're equal, ``prev_tag``
    is already an ancestor of ``new_tag`` (the common in-line case), so we return
    the tag itself to keep the pretty "Full Changelog" link; otherwise we return
    the merge-base SHA.
    """
    url = f"https://api.github.com/repos/{org_repo}/compare/{prev_tag}...{new_tag}"
    headers = {"Authorization": f"token {auth}"} if auth else {}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    base_sha = data.get("base_commit", {}).get("sha")
    merge_base_sha = data.get("merge_base_commit", {}).get("sha")
    if not merge_base_sha:
        # Defensive: fall back to the tag if the API shape is unexpected.
        return prev_tag
    if merge_base_sha == base_sha:
        # prev_tag is an ancestor of new_tag; keep the tag for a clean link.
        return prev_tag
    log(
        f"    note: {prev_tag} and {new_tag} diverged; starting window at "
        f"merge-base {merge_base_sha[:12]}"
    )
    return merge_base_sha


def submodule_entry(
    org_repo: str,
    display: str,
    since_ref: str | None,
    new_floor_tag: str,
    branch: str,
    auth: str | None,
) -> str:
    """Build one submodule's changelog block via Jupyter Releaser.

    Delegates to ``changelog.get_version_entry`` over the window
    ``since_ref..new_floor_tag`` so the label grouping and contributors list are
    identical to the releaser's own changelog. ``since_ref`` is the merge-base of
    the two floors (see window_start), not necessarily the previous-floor tag.
    The section heading is ``display`` (the submodule name), not a version.
    """
    entry = changelog.get_version_entry(
        ref=new_floor_tag,
        branch=branch,
        repo=org_repo,
        version=display,
        since=since_ref,
        until=new_floor_tag,
        auth=auth,
    )
    return entry.strip()


def build_page(
    version: str,
    repo_root: str,
    manifest_path: str,
    pyproject_path: str,
    target_branch: str,
    auth: str | None,
) -> str:
    """Assemble the full Markdown page for ``version``."""
    version = normalize_version(version)

    with open(manifest_path, encoding="utf-8") as f:
        manifest: dict[str, str] = json.load(f)

    with open(pyproject_path, encoding="utf-8") as f:
        new_floors = load_floors_from_text(f.read())

    prev_tag = previous_release_tag(repo_root, version, target_branch)
    if prev_tag is None:
        log(
            f"warning: found no official release before {version} on "
            f"'{target_branch}'; every submodule window will start from its "
            f"first release."
        )
        prev_floors: dict[str, str] = {}
    else:
        log(f"Previous release on '{target_branch}': {prev_tag}")
        prev_floors = load_floors_from_text(
            show_file_at(repo_root, prev_tag, "pyproject.toml")
        )

    sections: list[str] = []
    unchanged: list[str] = []
    skipped: list[str] = []

    for pypi_name, org_repo in manifest.items():
        key = _norm(pypi_name)
        repo = org_repo.split("/", 1)[1]
        url = f"https://github.com/{org_repo}.git"

        new_floor = new_floors.get(key)
        if new_floor is None:
            log(
                f"warning: {pypi_name} not a dependency floor in {pyproject_path}; skipping"
            )
            skipped.append(repo)
            continue

        prev_floor = prev_floors.get(key)

        # Unchanged floor ⇒ no new subpackage code shipped in this release.
        if prev_floor is not None and Version(prev_floor) == Version(new_floor):
            log(f"  {pypi_name}: floor unchanged at {new_floor}; no PRs")
            unchanged.append(f"`{repo}` (`v{new_floor}`)")
            continue

        tags = list_tags(url)
        new_floor_tag = resolve_floor_tag(new_floor, tags)
        if new_floor_tag is None:
            log(
                f"warning: {pypi_name} floor {new_floor} has no matching tag in "
                f"{org_repo}; skipping"
            )
            skipped.append(repo)
            continue

        prev_floor_tag = (
            resolve_floor_tag(prev_floor, tags) if prev_floor is not None else None
        )
        if prev_floor is not None and prev_floor_tag is None:
            log(
                f"warning: {pypi_name} previous floor {prev_floor} has no matching "
                f"tag in {org_repo}; starting window from first release"
            )

        # Start the PR window at where the two floors last shared history (their
        # merge-base), not the raw previous-floor tag — see window_start. In the
        # common in-line case this is just prev_floor_tag.
        since_ref = (
            window_start(org_repo, prev_floor_tag, new_floor_tag, auth)
            if prev_floor_tag
            else None
        )

        branch = default_branch(url)
        window = (
            f"{prev_floor_tag}..{new_floor_tag}"
            if prev_floor_tag
            else f"→ {new_floor_tag}"
        )
        log(f"  {pypi_name}: {window} (branch {branch})")

        display = f"{repo} ({window})"
        sections.append(
            submodule_entry(org_repo, display, since_ref, new_floor_tag, branch, auth)
        )

    header = [
        f"# {version}",
        "",
        f"Release notes for Jupyter AI **{version}**, aggregated from the "
        "subpackages whose version floors advanced in this release.",
    ]
    if prev_tag is not None:
        header.append(
            f"Each subpackage section covers the pull requests merged between its "
            f"floor at the previous release ({prev_tag}) and its floor at {version}."
        )
    body = ["\n".join(header)]

    if sections:
        body.append("\n\n".join(sections))
    else:
        body.append("_No subpackage version floors advanced in this release._")

    if unchanged:
        body.append(
            "## Unchanged subpackages\n\n"
            "The following subpackages did not advance their version floor in "
            "this release:\n\n" + "\n".join(f"- {u}" for u in sorted(unchanged))
        )
    if skipped:
        body.append(
            "## Not resolved\n\n"
            "These subpackages could not be resolved to a release window "
            "(see the generation log):\n\n"
            + "\n".join(f"- `{s}`" for s in sorted(skipped))
        )

    return "\n\n".join(body).strip() + "\n"


TOCTREE_RE = re.compile(
    r"(```\{toctree\}\n(?:.*\n)*?)(```)",
    re.MULTILINE,
)


def update_index_toctree(index_path: str, stem: str) -> None:
    """Ensure ``stem`` is listed in the releases index toctree.

    Entries are kept newest-first (descending PEP 440 order). The insert is
    idempotent: re-running for an existing version leaves the toctree unchanged.
    """
    with open(index_path, encoding="utf-8") as f:
        text = f.read()

    match = TOCTREE_RE.search(text)
    if not match:
        raise RuntimeError(f"no toctree block found in {index_path}")

    block = match.group(1)
    lines = block.splitlines()
    # Directive line + option lines (":opt:") stay put; the rest are entries.
    head: list[str] = []
    entries: list[str] = []
    for line in lines:
        stripped = line.strip()
        if (
            not stripped
            or stripped.startswith("```{toctree}")
            or stripped.startswith(":")
        ):
            head.append(line)
        else:
            entries.append(stripped)

    if stem not in entries:
        entries.append(stem)

    def sort_key(entry: str) -> Version:
        try:
            return Version(entry.lstrip("v"))
        except InvalidVersion:
            return Version("0")

    entries = sorted(set(entries), key=sort_key, reverse=True)

    new_block = "\n".join([*head, *entries]) + "\n"
    new_text = text[: match.start(1)] + new_block + text[match.end(1) :]
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(new_text)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--version", required=True, help="new version, e.g. v3.1.0 or v3.0.4"
    )
    parser.add_argument(
        "--repo-root", default=".", help="jupyter-ai checkout root (default: .)"
    )
    parser.add_argument(
        "--target-branch",
        default="main",
        help="branch the release targets (default: main)",
    )
    parser.add_argument(
        "--manifest",
        help="path to submodules/manifest.json (default: <repo-root>/submodules/manifest.json)",
    )
    parser.add_argument(
        "--pyproject",
        help="path to pyproject.toml (default: <repo-root>/pyproject.toml)",
    )
    parser.add_argument(
        "--output-dir", help="releases dir (default: <repo-root>/docs/source/releases)"
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="print the page to stdout instead of writing files (preview)",
    )
    args = parser.parse_args()

    repo_root = os.path.abspath(args.repo_root)
    manifest = args.manifest or os.path.join(repo_root, "submodules", "manifest.json")
    pyproject = args.pyproject or os.path.join(repo_root, "pyproject.toml")
    output_dir = args.output_dir or os.path.join(
        repo_root, "docs", "source", "releases"
    )

    auth = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not auth:
        log(
            "warning: no GITHUB_TOKEN/GH_TOKEN set; GitHub API calls may be rate-limited"
        )

    version = normalize_version(args.version)
    page = build_page(version, repo_root, manifest, pyproject, args.target_branch, auth)

    if args.stdout:
        print(page)
        return 0

    os.makedirs(output_dir, exist_ok=True)
    page_path = os.path.join(output_dir, f"{version}.md")
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(page)
    log(f"Wrote {page_path}")

    index_path = os.path.join(output_dir, "index.md")
    if os.path.exists(index_path):
        update_index_toctree(index_path, version)
        log(f"Updated {index_path} toctree")
    else:
        log(f"warning: {index_path} does not exist; not updating toctree")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
