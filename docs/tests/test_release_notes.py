"""Unit tests for the shared version/tag resolution helpers.

These cover the pure logic in ``_submodule_versions.py`` (floor extraction,
range/floor -> tag resolution, pyproject parsing) and the release-notes page
assembly in ``generate_release_notes.py`` that doesn't hit the network
(toctree insertion, previous-release-tag selection). No git or GitHub calls.

Run with: ``pytest docs/tests/test_release_notes.py`` (or the whole
``pytest docs/tests`` suite, as CI does).
"""

import json
import os
import subprocess
import sys

import pytest

# The modules under test live in the repo's scripts/ dir (docs/tests/ -> repo
# root -> scripts).
_SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"
)
sys.path.insert(0, _SCRIPTS_DIR)

import _submodule_versions as sv
import generate_release_notes as gen

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


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_window_start_inline_returns_tag(monkeypatch):
    # prev_tag is an ancestor of new_tag: base_commit == merge_base_commit.
    payload = {
        "base_commit": {"sha": "aaa"},
        "merge_base_commit": {"sha": "aaa"},
    }
    monkeypatch.setattr(gen.requests, "get", lambda *a, **k: _FakeResponse(payload))
    assert gen.window_start("org/repo", "v0.2.5", "v0.3.0", "tok") == "v0.2.5"


def test_window_start_diverged_returns_merge_base(monkeypatch):
    # Divergent branches: merge_base differs from prev_tag's own commit.
    payload = {
        "base_commit": {"sha": "aaa"},
        "merge_base_commit": {"sha": "bbb"},
    }
    monkeypatch.setattr(gen.requests, "get", lambda *a, **k: _FakeResponse(payload))
    assert gen.window_start("org/repo", "v0.2.6", "v0.3.1", "tok") == "bbb"


def test_window_start_missing_merge_base_falls_back(monkeypatch):
    payload = {"base_commit": {"sha": "aaa"}}
    monkeypatch.setattr(gen.requests, "get", lambda *a, **k: _FakeResponse(payload))
    assert gen.window_start("org/repo", "v0.2.5", "v0.3.0", "tok") == "v0.2.5"


def test_normalize_version_adds_v_prefix():
    assert gen.normalize_version("3.1.0") == "v3.1.0"
    assert gen.normalize_version("v3.1.0") == "v3.1.0"
    assert gen.normalize_version("  3.0.4 ") == "v3.0.4"


# A representative get_version_entry() block: heading, Full Changelog link,
# grouped PR bullets, and the contributors footer we drop.
_ENTRY = """## v0.3.0

([Full Changelog](https://github.com/org/repo/compare/v0.2.5...v0.3.0))

### Enhancements made

- Add a thing [#10](https://github.com/org/repo/pull/10) ([@a](https://github.com/a))

### Bugs fixed

- Fix a thing [#11](https://github.com/org/repo/pull/11) ([@b](https://github.com/b))

### Contributors to this release

The following people contributed discussions, new ideas, code and documentation contributions, and review.
See [our definition of contributors](https://github-activity.readthedocs.io/).

([GitHub contributors page for this release](https://github.com/org/repo/graphs/contributors))

@a ([activity](https://x)) | @b ([activity](https://y))"""


def test_demote_headings_shifts_all_levels():
    text = "## `repo`\n\nsome prose\n\n### Enhancements made\n\n- a bullet"
    out = gen.demote_headings(text)
    assert "### `repo`" in out
    assert "#### Enhancements made" in out
    # Non-heading lines untouched.
    assert "some prose" in out
    assert "- a bullet" in out


def test_demote_headings_caps_at_h6():
    assert gen.demote_headings("###### deep") == "###### deep"


def test_strip_to_pr_groups_drops_heading_link_and_contributors():
    out = gen.strip_to_pr_groups(_ENTRY)
    # PR groups kept
    assert "### Enhancements made" in out
    assert "- Add a thing [#10]" in out
    assert "### Bugs fixed" in out
    # Heading, Full Changelog link, and contributors footer removed
    assert "## v0.3.0" not in out
    assert "Full Changelog" not in out
    assert "Contributors to this release" not in out
    assert "@a (" not in out
    assert "graphs/contributors" not in out


def test_strip_to_pr_groups_keeps_subsection_headings():
    # ### headings must survive; only the top-level ## heading is dropped.
    out = gen.strip_to_pr_groups(_ENTRY)
    assert out.count("###") == 2


def test_submodule_section_format(monkeypatch):
    monkeypatch.setattr(gen.changelog, "get_version_entry", lambda **k: _ENTRY)
    section = gen.submodule_section(
        org_repo="org/repo",
        repo="repo",
        prev_floor="0.2.5",
        new_floor="0.3.0",
        new_floor_tag="v0.3.0",
        since_ref="v0.2.5",
        branch="main",
        auth="tok",
    )
    lines = section.splitlines()
    assert lines[0] == "## `repo`"
    assert (
        "Upgraded from `v0.2.5` → `v0.3.0`. "
        "([See full changelog](https://github.com/org/repo/releases))"
    ) in section
    # PR groups present; contributors footer gone.
    assert "- Add a thing [#10]" in section
    assert "Contributors to this release" not in section


def test_submodule_section_added_when_no_prev_floor(monkeypatch):
    monkeypatch.setattr(gen.changelog, "get_version_entry", lambda **k: _ENTRY)
    section = gen.submodule_section(
        org_repo="org/repo",
        repo="repo",
        prev_floor=None,
        new_floor="0.3.0",
        new_floor_tag="v0.3.0",
        since_ref=None,
        branch="main",
        auth="tok",
    )
    assert "Added at `v0.3.0`." in section
    assert "Upgraded from" not in section


def test_submodule_section_optional_note(monkeypatch):
    monkeypatch.setattr(gen.changelog, "get_version_entry", lambda **k: _ENTRY)
    section = gen.submodule_section(
        org_repo="org/repo",
        repo="repo",
        prev_floor="0.2.5",
        new_floor="0.3.0",
        new_floor_tag="v0.3.0",
        since_ref="v0.2.5",
        branch="main",
        auth="tok",
        is_optional=True,
    )
    # Colon-fenced admonition (renders in Sphinx, reads as prose elsewhere) —
    # NOT a ```-fenced block, which plain Markdown shows as code.
    assert ":::{note}" in section
    assert "```{note}" not in section
    assert "optional package" in section


def test_submodule_section_no_optional_note_by_default(monkeypatch):
    monkeypatch.setattr(gen.changelog, "get_version_entry", lambda **k: _ENTRY)
    section = gen.submodule_section(
        org_repo="org/repo",
        repo="repo",
        prev_floor="0.2.5",
        new_floor="0.3.0",
        new_floor_tag="v0.3.0",
        since_ref="v0.2.5",
        branch="main",
        auth="tok",
    )
    assert "optional package" not in section


def test_optional_only_names_excludes_core_deps():
    text = """
[project]
name = "jupyter_ai"
dependencies = ["core_pkg>=1.0", "shared_pkg>=1.0"]

[project.optional-dependencies]
magics = ["opt_pkg>=0.1", "shared_pkg>=1.0"]
jupyternaut = ["jupyter_ai_jupyternaut>=0.1.0b0,<0.2.0"]
"""
    result = sv.optional_only_names(text)
    # Optional-only packages are reported...
    assert "opt_pkg" in result
    assert "jupyter_ai_jupyternaut" in result
    # ...but a package that is also a core dep is NOT (it's effectively required).
    assert "shared_pkg" not in result
    assert "core_pkg" not in result


CORE_PYPROJECT = """
[project]
name = "jupyter-ai-core"
dependencies = [
  "jupyterlab>=4.0.0,<5",
  "jupyter_server_mcp>=0.3.0,<0.4.0",
]
"""

AI_PYPROJECT = """
[project]
name = "jupyter_ai"
dependencies = [
  "jupyter_ai_core==3.2.0",
  "jupyter_ai_router>=0.1.1,<0.2.0",
]

[project.optional-dependencies]
rtc = ["jupyter_server_mcp>=0.3.1"]
magics = ["jupyter_ai_litellm>=0.1.0,<0.2.0"]
"""


def test_load_floors_merges_several_pyprojects():
    floors = sv.load_floors_from_text(CORE_PYPROJECT, AI_PYPROJECT)
    assert floors["jupyter_ai_router"] == "0.1.1"
    assert floors["jupyter_ai_litellm"] == "0.1.0"
    # Listed by both packages: the ranges intersect, so the higher floor wins.
    assert floors["jupyter_server_mcp"] == "0.3.1"


def test_optional_only_names_across_pyprojects():
    result = sv.optional_only_names(CORE_PYPROJECT, AI_PYPROJECT)
    assert result == {"jupyter_ai_litellm"}


def _commit_all(repo, message):
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "--no-gpg-sign",
            "-qm",
            message,
        ],
        check=True,
    )


def test_pyproject_texts_at_reads_packages_and_legacy_root(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "pyproject.toml").write_text(AI_PYPROJECT, encoding="utf-8")
    _commit_all(tmp_path, "single package at the root")
    subprocess.run(["git", "-C", str(tmp_path), "tag", "v3.2.0"], check=True)

    (tmp_path / "pyproject.toml").write_text('[project]\nname = "root"\n')
    for path, text in zip(sv.PYPROJECT_PATHS, (CORE_PYPROJECT, AI_PYPROJECT)):
        (tmp_path / path).parent.mkdir(parents=True)
        (tmp_path / path).write_text(text, encoding="utf-8")
    _commit_all(tmp_path, "packages under python/")

    assert gen.pyproject_texts_at(str(tmp_path), "v3.2.0") == [AI_PYPROJECT.strip()]
    assert gen.pyproject_texts_at(str(tmp_path), "HEAD") == [
        CORE_PYPROJECT.strip(),
        AI_PYPROJECT.strip(),
    ]


def test_submodule_section_omits_empty_pr_body(monkeypatch):
    monkeypatch.setattr(
        gen.changelog, "get_version_entry", lambda **k: "## v0.3.0\n\nNo merged PRs"
    )
    section = gen.submodule_section(
        org_repo="org/repo",
        repo="repo",
        prev_floor="0.2.5",
        new_floor="0.3.0",
        new_floor_tag="v0.3.0",
        since_ref="v0.2.5",
        branch="main",
        auth="tok",
    )
    # Heading + summary only; no dangling "No merged PRs".
    assert "## `repo`" in section
    assert "No merged PRs" not in section


def test_build_page_header(monkeypatch, tmp_path):
    # No network: stub the previous-release lookup, tag/branch resolution, and
    # each submodule section.
    monkeypatch.setattr(gen, "previous_release_tag", lambda *a, **k: "v3.0.1")
    monkeypatch.setattr(gen, "show_file_at", lambda *a, **k: PREV_PYPROJECT)
    monkeypatch.setattr(gen, "list_tags", lambda url: ["v0.0.5", "v0.0.6"])
    monkeypatch.setattr(gen, "default_branch", lambda url: "main")
    monkeypatch.setattr(gen, "window_start", lambda *a, **k: "v0.0.5")
    monkeypatch.setattr(
        gen,
        "submodule_section",
        lambda org_repo, repo, *a, **k: f"## `{repo}`\n\nUpgraded stub.",
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"jupyter_ai_router": "org/jupyter-ai-router"}', encoding="utf-8"
    )
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(NEW_PYPROJECT, encoding="utf-8")

    page = gen.build_page(
        version="v3.1.0",
        repo_root=str(tmp_path),
        manifest_path=str(manifest),
        pyproject_paths=[str(pyproject)],
        target_branch="main",
        auth="tok",
        published_date="July 22, 2026",
    )
    assert "# v3.1.0" in page
    assert "*Published on July 22, 2026.*" in page
    assert gen.CONTRIBUTORS_NOTE in page
    # Two AUTO regions (header + changelog) and one SUMMARY region.
    assert page.count(gen.AUTO_BEGIN) == 2
    assert page.count(gen.AUTO_END) == 2
    assert page.count(gen.SUMMARY_BEGIN) == 1
    assert page.count(gen.SUMMARY_END) == 1
    # The changelog sits inside the second auto region under a "## Full
    # changelog" heading, after the summary. Subpackage headings are demoted one
    # level (## -> ###) so they nest under it.
    assert "## Full changelog" in page
    assert "### `jupyter-ai-router`" in page
    assert page.index("## Full changelog") > page.index(gen.SUMMARY_END)
    # Only one H1 (the version title); Full changelog is H2, not a second H1.
    assert page.count("\n# ") + page.startswith("# ") == 1

    # The explanatory blurb lives inside the editable SUMMARY region (so a
    # contributor can trim it), NOT in an auto region.
    summary = page.split(gen.SUMMARY_BEGIN, 1)[1].split(gen.SUMMARY_END, 1)[0]
    assert (
        "auto-generated release notes for Jupyter AI **v3.1.0** from the `main` branch"
        in summary
    )
    assert "floor at the previous release (v3.0.1)" in summary
    assert gen.CONTRIBUTORS_NOTE in summary


def test_build_page_covers_extra_changelog_repos(monkeypatch, tmp_path):
    # A changelog-only repo (not a doc submodule, so absent from the manifest)
    # still gets a section, so its PRs aren't dropped from the release notes.
    monkeypatch.setattr(gen, "previous_release_tag", lambda *a, **k: "v3.0.1")
    monkeypatch.setattr(
        gen,
        "show_file_at",
        lambda *a, **k: (
            '[project]\nname = "jupyter_ai"\ndependencies = ['
            '"jupyter_ai_router>=0.0.5,<0.1.0", "extra_pkg>=0.1.0,<0.2.0"]\n'
        ),
    )
    monkeypatch.setattr(
        gen, "list_tags", lambda url: ["v0.0.5", "v0.0.6", "v0.1.0", "v0.2.0"]
    )
    monkeypatch.setattr(gen, "default_branch", lambda url: "main")
    monkeypatch.setattr(gen, "window_start", lambda *a, **k: "v0.1.0")
    monkeypatch.setattr(
        gen,
        "submodule_section",
        lambda org_repo, repo, *a, **k: f"## `{repo}`\n\nUpgraded stub.",
    )
    monkeypatch.setattr(
        gen, "EXTRA_CHANGELOG_REPOS", {"extra_pkg": "some-org/extra-pkg"}
    )

    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"jupyter_ai_router": "org/jupyter-ai-router"}', encoding="utf-8"
    )
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "jupyter_ai"\ndependencies = ['
        '"jupyter_ai_router>=0.0.6,<0.1.0", "extra_pkg>=0.2.0,<0.3.0"]\n',
        encoding="utf-8",
    )

    page = gen.build_page(
        version="v3.1.0",
        repo_root=str(tmp_path),
        manifest_path=str(manifest),
        pyproject_paths=[str(pyproject)],
        target_branch="main",
        auth="tok",
        published_date="July 22, 2026",
    )
    # Both the manifest repo and the changelog-only repo are covered.
    assert "### `extra-pkg`" in page
    assert "### `jupyter-ai-router`" in page
    # Extras lead, so the most user-facing package heads the changelog.
    assert page.index("### `extra-pkg`") < page.index("### `jupyter-ai-router`")


def test_extra_changelog_repos_disjoint_from_manifest():
    # A repo in both places would be pinned as a doc submodule AND listed here;
    # the manifest is the right home for that, so the two must not overlap.
    manifest_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "submodules",
        "manifest.json",
    )
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    overlap = set(manifest) & set(gen.EXTRA_CHANGELOG_REPOS)
    assert not overlap, f"registered as both doc submodule and extra: {overlap}"
    assert "jupyter_live_content" in gen.EXTRA_CHANGELOG_REPOS


def test_core_names_reads_core_deps_only():
    names = sv.core_names(CORE_PYPROJECT, AI_PYPROJECT)
    assert names == {
        "jupyterlab",
        "jupyter_server_mcp",
        "jupyter_ai_core",
        "jupyter_ai_router",
    }
    # Extras are not core, even when they re-list a core package.
    assert "jupyter_ai_litellm" not in names


def test_unregistered_core_dependencies_normalizes_and_exempts(monkeypatch):
    monkeypatch.setattr(gen, "EXTRA_CHANGELOG_REPOS", {"Extra-Pkg": "o/extra-pkg"})
    monkeypatch.setattr(gen, "CHANGELOG_EXEMPT_DEPENDENCIES", {"skipped-pkg"})
    text = """
[project]
name = "jupyter_ai"
dependencies = [
  "jupyter-ai-router>=0.1.0",
  "extra_pkg>=0.1.0",
  "Skipped_Pkg>=1.0",
  "forgotten_pkg>=0.0.1",
]

[project.optional-dependencies]
magics = ["opt_pkg>=0.1"]
"""
    manifest = {"jupyter_ai_router": "o/jupyter-ai-router"}
    # Spelling differences (-/_ and case) between the sources do not count as
    # unregistered; exempt names are skipped; optional extras are not checked.
    assert gen.unregistered_core_dependencies(manifest, text) == {"forgotten_pkg"}


def test_unregistered_core_dependencies_across_pyprojects():
    manifest = {"jupyter_ai_router": "o/jupyter-ai-router"}
    # jupyterlab and jupyter_ai_core are exempt by default; jupyter_server_mcp
    # (a jupyter-ai-core dependency) is the one that is really missing.
    assert gen.unregistered_core_dependencies(
        manifest, CORE_PYPROJECT, AI_PYPROJECT
    ) == {"jupyter_server_mcp"}


def test_build_page_warns_about_unregistered_core_dependency(monkeypatch, tmp_path):
    monkeypatch.setattr(gen, "previous_release_tag", lambda *a, **k: None)
    monkeypatch.setattr(gen, "list_tags", lambda url: ["v0.0.6"])
    monkeypatch.setattr(gen, "default_branch", lambda url: "main")
    monkeypatch.setattr(
        gen,
        "submodule_section",
        lambda org_repo, repo, *a, **k: f"## `{repo}`\n\nstub.",
    )
    logged: list[str] = []
    monkeypatch.setattr(gen, "log", logged.append)

    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"jupyter_ai_router": "org/jupyter-ai-router"}', encoding="utf-8"
    )
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "jupyter_ai"\ndependencies = ['
        '"jupyter_ai_router>=0.0.6,<0.1.0", "forgotten_pkg>=0.2.0,<0.3.0"]\n',
        encoding="utf-8",
    )
    gen.build_page(
        version="v3.1.0",
        repo_root=str(tmp_path),
        manifest_path=str(manifest),
        pyproject_paths=[str(pyproject)],
        target_branch="main",
        auth="tok",
        published_date="July 22, 2026",
    )
    warnings = [m for m in logged if "no changelog coverage" in m]
    assert len(warnings) == 1
    assert "forgotten_pkg" in warnings[0]
    assert "jupyter_ai_router" not in warnings[0]


def test_every_core_dependency_is_registered_for_changelog():
    # The guard the generator's warning backs up: every non-optional dependency
    # of the real packages must be a doc submodule, a changelog-only repo or an
    # explicit exemption — otherwise its PRs silently vanish from the release
    # notes (the way jupyter_live_content's did in v3.2.0).
    repo_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    with open(
        os.path.join(repo_root, "submodules", "manifest.json"), encoding="utf-8"
    ) as f:
        manifest = json.load(f)
    texts = []
    for path in sv.PYPROJECT_PATHS:
        with open(os.path.join(repo_root, path), encoding="utf-8") as f:
            texts.append(f.read())
    missing = gen.unregistered_core_dependencies(manifest, *texts)
    assert not missing, (
        f"core dependencies with no changelog coverage: {sorted(missing)}; add "
        "each to submodules/manifest.json, EXTRA_CHANGELOG_REPOS or "
        "CHANGELOG_EXEMPT_DEPENDENCIES in scripts/generate_release_notes.py"
    )


def test_changelog_exemptions_are_not_also_registered():
    registered = {sv._norm(n) for n in gen.EXTRA_CHANGELOG_REPOS}
    exempt = {sv._norm(n) for n in gen.CHANGELOG_EXEMPT_DEPENDENCIES}
    assert not registered & exempt


def test_default_summary_omits_window_line_without_prev_tag():
    # No previous release ⇒ no "PRs between floors" sentence, but the note stays.
    s = gen.default_summary("v3.1.0", "main", prev_tag=None)
    assert "auto-generated release notes" in s
    assert "floor at the previous release" not in s
    assert gen.CONTRIBUTORS_NOTE in s


# Floors: router advanced 0.0.5 -> 0.0.6, so it gets a section.
PREV_PYPROJECT = """
[project]
name = "jupyter_ai"
dependencies = ["jupyter_ai_router>=0.0.5,<0.1.0"]
"""
NEW_PYPROJECT = """
[project]
name = "jupyter_ai"
dependencies = ["jupyter_ai_router>=0.0.6,<0.1.0"]
"""


# A minimal page shaped like build_page output: two AUTO regions around a
# contributor-owned SUMMARY region.
def _page(header_body, summary_body, changelog_body):
    return "\n\n".join(
        [
            gen.wrap_auto(header_body),
            f"{gen.SUMMARY_BEGIN}\n{summary_body}\n{gen.SUMMARY_END}",
            gen.wrap_auto(changelog_body),
        ]
    )


def test_regenerate_auto_regions_preserves_summary_and_out_of_band_edits():
    existing = (
        _page(
            "# v3.1.0\nold date",
            "## Highlights\n\n- edited by a human",
            "old changelog",
        )
        + "\n\n> a note a contributor added outside the auto regions\n"
    )
    fresh = _page("# v3.1.0\nnew date", gen.CONTRIBUTORS_NOTE, "new changelog")

    merged = gen.regenerate_auto_regions(existing, fresh)

    # Auto regions took the fresh content...
    assert "new date" in merged
    assert "new changelog" in merged
    assert "old date" not in merged
    assert "old changelog" not in merged
    # ...but the human summary and the out-of-band note survived.
    assert "## Highlights\n\n- edited by a human" in merged
    assert "a note a contributor added outside the auto regions" in merged
    # Default summary is NOT reintroduced when a human already replaced it.
    assert gen.CONTRIBUTORS_NOTE not in merged


def test_regenerate_auto_regions_aborts_on_region_count_mismatch():
    # Contributor removed one AUTO region's markers -> counts differ -> abort.
    existing = f"{gen.AUTO_BEGIN}\nonly one region\n{gen.AUTO_END}\n\nsummary text"
    fresh = _page("h", gen.CONTRIBUTORS_NOTE, "c")
    with pytest.raises(gen.MarkerError):
        gen.regenerate_auto_regions(existing, fresh)


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
