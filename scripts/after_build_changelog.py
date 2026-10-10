#!/usr/bin/env python
"""Insert the standard Jupyter AI release-notes preamble into CHANGELOG.md.

Runs as a jupyter-releaser ``after-build-changelog`` hook (see the
``[tool.jupyter-releaser.hooks]`` table in pyproject.toml). During "Step 1:
Prep Release", ``build-changelog`` writes the new version's entry into
CHANGELOG.md between the START/END markers; this script adds a fixed blurb just
under the ``## <version>`` heading, pointing readers to the full release notes
published on the docs site.

Only final releases get the blurb: the docs ``releases/vX.Y.Z.html`` page and
the ``stable`` docs alias exist only for finals, so linking to them from a
prerelease changelog would 404.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CHANGELOG = Path("CHANGELOG.md")
START = "<!-- <START NEW CHANGELOG ENTRY> -->"
END = "<!-- <END NEW CHANGELOG ENTRY> -->"

# Substring unique to the blurb, used to make re-runs idempotent.
SENTINEL = "for the complete v"


def build_preamble(version: str) -> str:
    """Return the release-notes preamble for a final ``version`` (no leading v)."""
    return (
        f"**[Click here](https://jupyter-ai.readthedocs.io/en/stable/releases/"
        f"v{version}.html) for the complete v{version} release notes, now "
        "published on our official documentation site.**\n\n"
        "The changelog that follows is specific to the `jupyterlab/jupyter-ai` "
        "repo - they mostly include updates to documentation, version ranges, "
        "and GitHub workflows. All source code now lives in Jupyter AI's "
        "various subpackages, whose changes are reported in the official "
        "documentation linked above.\n\n"
        "---\n"
    )


def main() -> int:
    text = CHANGELOG.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("error: changelog markers not found", file=sys.stderr)
        return 1

    start, end = text.index(START), text.index(END)
    block = text[start:end]

    match = re.search(r"^## (\S+)", block, flags=re.MULTILINE)
    if not match:
        print("error: no version heading in new changelog entry", file=sys.stderr)
        return 1
    version = match.group(1)

    # Skip prereleases (e.g. 3.2.0rc1, 3.2.0a1): no stable docs page exists.
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        print(f"Skipping preamble for prerelease {version}.")
        return 0

    if SENTINEL in block:
        print("Preamble already present; nothing to do.")
        return 0

    insert_at = start + match.end()
    text = text[:insert_at] + "\n\n" + build_preamble(version) + text[insert_at:]
    CHANGELOG.write_text(text, encoding="utf-8")
    print(f"Inserted release-notes preamble for v{version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
