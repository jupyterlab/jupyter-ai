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
import datetime
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

# The page is split into auto-generated regions and a contributor-owned region.
# Each auto region is wrapped in AUTO markers; on a re-run only those regions are
# regenerated, and *everything else* on the page — the summary block and any prose
# a contributor added outside the auto regions — is preserved verbatim. This lets
# a re-run pick up a newly-merged subpackage PR without clobbering hand edits.
AUTO_BEGIN = "<!-- BEGIN AUTO-GENERATED (do not edit; regenerated on each run) -->"
AUTO_END = "<!-- END AUTO-GENERATED -->"
SUMMARY_BEGIN = (
    "<!-- BEGIN SUMMARY (contributors: edit freely; preserved on re-run) -->"
)
SUMMARY_END = "<!-- END SUMMARY -->"

CONTRIBUTORS_NOTE = (
    "CONTRIBUTORS: **Please replace this text with a human-readable summary of "
    "the changes. See `AGENTS.md` in the `jupyterlab/jupyter-ai` repo for more "
    "information.**"
)


def default_summary(version: str, target_branch: str, prev_tag: str | None) -> str:
    """Seed text for the contributor-owned SUMMARY region on a first run.

    This is written verbatim only when the page doesn't exist yet; on re-runs the
    whole region is preserved, so a contributor can edit or delete any of it —
    including the "auto-generated notes" explanation, which is boilerplate they
    may not want once they've written a real summary.
    """
    blurb = (
        f"These are the auto-generated release notes for Jupyter AI "
        f"**{version}** from the `{target_branch}` branch, aggregated from the "
        f"subpackages whose version floors advanced in this release."
    )
    if prev_tag is not None:
        blurb += (
            f" Each subpackage section covers the pull requests merged between "
            f"its floor at the previous release ({prev_tag}) and its floor at "
            f"{version}."
        )
    return f"{blurb}\n\n{CONTRIBUTORS_NOTE}"


# One auto region: the begin/end markers and everything between them.
_AUTO_RE = re.compile(
    re.escape(AUTO_BEGIN) + r".*?" + re.escape(AUTO_END),
    re.DOTALL,
)


class MarkerError(RuntimeError):
    """Raised when an existing page's AUTO markers don't match what we expect."""


def wrap_auto(inner: str) -> str:
    """Wrap ``inner`` in the auto-generated-region markers."""
    return f"{AUTO_BEGIN}\n{inner.strip()}\n{AUTO_END}"


def regenerate_auto_regions(existing_text: str, fresh_text: str) -> str:
    """Return ``existing_text`` with its auto regions swapped for ``fresh_text``'s.

    Both pages carry the same number of AUTO regions (the header block and the
    changelog block). We replace each auto region in the existing page, in
    document order, with the corresponding freshly generated one — leaving every
    byte outside the auto regions (the contributor-owned summary and any other
    hand edits) untouched.

    Raises ``MarkerError`` if the existing page's auto-region count doesn't match
    the freshly generated page's, so a re-run aborts rather than silently
    overwriting a page whose markers a contributor removed or duplicated.
    """
    fresh_regions = _AUTO_RE.findall(fresh_text)
    existing_regions = list(_AUTO_RE.finditer(existing_text))
    if len(existing_regions) != len(fresh_regions):
        raise MarkerError(
            f"existing page has {len(existing_regions)} AUTO-GENERATED region(s) "
            f"but a fresh page has {len(fresh_regions)}; refusing to regenerate "
            f"over a page whose auto markers were removed or altered"
        )

    out: list[str] = []
    last = 0
    for match, fresh_region in zip(existing_regions, fresh_regions):
        out.append(existing_text[last : match.start()])
        out.append(fresh_region)
        last = match.end()
    out.append(existing_text[last:])
    return "".join(out)


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


def strip_to_pr_groups(entry: str) -> str:
    """Keep only the label-grouped PR bullets from a ``get_version_entry`` block.

    ``get_version_entry`` returns a ``## <heading>`` line, a
    ``([Full Changelog](...))`` link, the ``### Enhancements made`` /
    ``### Bugs fixed`` / ... groups, then a ``### Contributors to this release``
    footer. We render our own heading + version-change line + changelog link, and
    every PR bullet already credits its authors inline, so we drop the heading,
    the Full Changelog link, and the whole contributors footer — keeping just the
    grouped PR bullets.
    """
    # Cut the contributors footer (and everything after it).
    entry = re.split(r"\n#{1,6}\s+Contributors to this release", entry, maxsplit=1)[0]

    kept: list[str] = []
    for line in entry.splitlines():
        stripped = line.strip()
        # Drop the top-level "## <heading>" line (### subsection headings, which
        # don't match this prefix, are kept).
        if stripped.startswith("## "):
            continue
        # Drop the "([Full Changelog](...))" link beneath it.
        if stripped.lower().startswith("([full changelog]"):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def submodule_section(
    org_repo: str,
    repo: str,
    prev_floor: str | None,
    new_floor: str,
    new_floor_tag: str,
    since_ref: str | None,
    branch: str,
    auth: str | None,
) -> str:
    """Build one submodule's section.

    The PR bullets come from Jupyter Releaser's ``get_version_entry`` over the
    window ``since_ref..new_floor_tag`` (same label grouping the releaser uses;
    ``since_ref`` is the merge-base — see ``window_start``). We wrap them in our
    own heading — the package name in a code span — with a version-change line
    and a link to the subpackage's GitHub release page for the new tag.
    """
    entry = changelog.get_version_entry(
        ref=new_floor_tag,
        branch=branch,
        repo=org_repo,
        version=new_floor_tag,
        since=since_ref,
        until=new_floor_tag,
        auth=auth,
    )
    pr_groups = strip_to_pr_groups(entry.strip())

    releases_url = f"https://github.com/{org_repo}/releases/tag/{new_floor_tag}"
    changelog_link = f"([See full changelog]({releases_url}))"
    if prev_floor:
        summary = f"Upgraded from `v{prev_floor}` → `v{new_floor}`. {changelog_link}"
    else:
        summary = f"Added at `v{new_floor}`. {changelog_link}"

    parts = [f"## `{repo}`", summary]
    # An advanced floor with no user-facing PRs (e.g. only bot/pre-commit PRs,
    # which get_version_entry filters out) leaves nothing to list.
    if pr_groups and pr_groups != "No merged PRs":
        parts.append(pr_groups)
    return "\n\n".join(parts)


def build_page(
    version: str,
    repo_root: str,
    manifest_path: str,
    pyproject_path: str,
    target_branch: str,
    auth: str | None,
    published_date: str,
) -> str:
    """Assemble a fresh Markdown page for ``version``.

    ``published_date`` is a pre-formatted human string (e.g. "July 22, 2026")
    passed in by the caller so the page is deterministic and testable.

    The page has two AUTO-GENERATED regions (a header block and the changelog
    block) with a contributor-owned SUMMARY region between them. On a re-run the
    caller regenerates only the AUTO regions (see ``regenerate_auto_regions``),
    preserving the summary and any other hand edits; this function always emits
    the default summary, used verbatim only on the first run.
    """
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

        sections.append(
            submodule_section(
                org_repo,
                repo,
                prev_floor,
                new_floor,
                new_floor_tag,
                since_ref,
                branch,
                auth,
            )
        )

    # AUTO region 1: title + publication date. These are always accurate, so
    # they stay auto-generated. The explanatory blurb lives in the editable
    # summary below, not here, so contributors can trim it.
    header_auto = wrap_auto(
        "\n".join([f"# {version}", "", f"*Published on {published_date}.*"])
    )

    # Contributor-owned region: seeded with the blurb + call-to-action on a first
    # run, then preserved (and freely editable) across re-runs.
    summary_seed = default_summary(version, target_branch, prev_tag)
    summary_region = f"{SUMMARY_BEGIN}\n{summary_seed}\n{SUMMARY_END}"

    # AUTO region 2: the per-subpackage changelog.
    changelog: list[str] = []
    if sections:
        changelog.append("\n\n".join(sections))
    else:
        changelog.append("_No subpackage version floors advanced in this release._")
    if unchanged:
        changelog.append(
            "## Unchanged subpackages\n\n"
            "The following subpackages did not advance their version floor in "
            "this release:\n\n" + "\n".join(f"- {u}" for u in sorted(unchanged))
        )
    if skipped:
        changelog.append(
            "## Not resolved\n\n"
            "These subpackages could not be resolved to a release window "
            "(see the generation log):\n\n"
            + "\n".join(f"- `{s}`" for s in sorted(skipped))
        )
    changelog_auto = wrap_auto("\n\n".join(changelog))

    return "\n\n".join([header_auto, summary_region, changelog_auto]).strip() + "\n"


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
        "--date",
        help=(
            "publication date to stamp on the page, as YYYY-MM-DD "
            "(default: today). Rendered as e.g. 'July 22, 2026'."
        ),
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

    if args.date:
        published = datetime.date.fromisoformat(args.date)
    else:
        published = datetime.date.today()
    # Cross-platform "July 22, 2026" (no %-d / %#d portability worries).
    published_date = f"{published:%B} {published.day}, {published.year}"

    version = normalize_version(args.version)
    page_path = os.path.join(output_dir, f"{version}.md")

    fresh = build_page(
        version,
        repo_root,
        manifest,
        pyproject,
        args.target_branch,
        auth,
        published_date,
    )

    # Re-run: regenerate only the AUTO regions of the existing page, preserving
    # the contributor-owned summary and any other hand edits outside them. A
    # mismatch in auto-region count aborts (regenerate_auto_regions raises)
    # rather than overwriting a page whose markers were removed or altered.
    if os.path.exists(page_path):
        with open(page_path, encoding="utf-8") as f:
            existing = f.read()
        try:
            page = regenerate_auto_regions(existing, fresh)
        except MarkerError as e:
            log(f"error: {e} ({page_path})")
            return 1
        log(f"Regenerated auto sections; preserved hand edits in {page_path}")
    else:
        page = fresh

    if args.stdout:
        print(page)
        return 0

    os.makedirs(output_dir, exist_ok=True)
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
