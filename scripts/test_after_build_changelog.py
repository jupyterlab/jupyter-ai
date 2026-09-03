"""Tests for scripts/after_build_changelog.py (the after-build-changelog hook).

Self-contained and fast: no network, no jupyter-releaser. Verifies the two
properties that matter for the hook — it touches only the newest entry, and it
does nothing for prereleases — plus idempotency and the exact layout
(``## <version>`` heading kept, blurb, ``---``, then the rest of the entry).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parent / "after_build_changelog.py"

spec = importlib.util.spec_from_file_location("after_build_changelog", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# A changelog with a fresh entry between the markers and an older entry below
# the END marker. The older entry doubles as a tripwire: the hook must not
# touch anything outside the new-entry block.
FINAL = """\
# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

## 3.4.5

([Full Changelog](https://github.com/jupyterlab/jupyter-ai/compare/v3.4.4...abc))

### Bugs fixed

- Fix a thing [#42](https://github.com/jupyterlab/jupyter-ai/pull/42) ([@x](https://github.com/x))

<!-- <END NEW CHANGELOG ENTRY> -->

## 3.4.4

Older entry, must not change.
"""

PRERELEASE = FINAL.replace("## 3.4.5", "## 3.5.0rc1")


def _run(tmp_path, monkeypatch, text):
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(text, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    rc = mod.main()
    return rc, changelog.read_text(encoding="utf-8")


def test_touches_only_the_new_entry(tmp_path, monkeypatch):
    rc, out = _run(tmp_path, monkeypatch, FINAL)
    assert rc == 0

    # Everything below the END marker is byte-for-byte unchanged.
    tail = out[out.index(mod.END) :]
    assert tail == FINAL[FINAL.index(mod.END) :]

    # The blurb is inserted exactly once, inside the new-entry block.
    block = out[out.index(mod.START) : out.index(mod.END)]
    assert out.count("for the complete v3.4.5 release notes") == 1
    assert "for the complete v3.4.5 release notes" in block


def test_layout_keeps_h2_then_blurb_then_separator_then_changelog(tmp_path, monkeypatch):
    _, out = _run(tmp_path, monkeypatch, FINAL)
    block = out[out.index(mod.START) : out.index(mod.END)]

    heading = block.index("## 3.4.5")
    blurb = block.index("for the complete v3.4.5 release notes")
    separator = block.index("\n---\n")
    full_changelog = block.index("([Full Changelog]")

    # ## <version>  ->  blurb  ->  ---  ->  (Full Changelog)
    assert heading < blurb < separator < full_changelog


def test_prerelease_is_a_noop(tmp_path, monkeypatch):
    rc, out = _run(tmp_path, monkeypatch, PRERELEASE)
    assert rc == 0
    assert out == PRERELEASE


def test_idempotent(tmp_path, monkeypatch):
    _, first = _run(tmp_path, monkeypatch, FINAL)
    # Re-running against already-processed content changes nothing.
    (tmp_path / "CHANGELOG.md").write_text(first, encoding="utf-8")
    assert mod.main() == 0
    assert (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8") == first
