#!/usr/bin/env python3
"""
Bump the version of every Python package in this repository, in lockstep.

Jupyter Releaser runs this as its version command, once per package listed in
`python_packages`. Each run computes the new version from the version committed
at HEAD, so the runs agree and the result is the same as a single run.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from packaging.version import Version

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILES = [
    "python/jupyter-ai-core/jupyter_ai_core/__init__.py",
    "python/jupyter-ai/jupyter_ai/__init__.py",
]
CORE_PIN_FILE = "python/jupyter-ai/pyproject.toml"
VERSION_RE = re.compile(r'^__version__ = "([^"]+)"$', re.MULTILINE)
CORE_PIN_RE = re.compile(r'"(jupyter[-_]ai[-_]core)==([^"]+)"')


def increment(current: Version, spec: str) -> Version:
    """
    Return the version for `spec`: an explicit version, or next, patch, minor, major.

    The keywords follow Jupyter Releaser's own rules for hatch projects.
    """
    if spec == "next" and current.pre:
        kind, number = current.pre
        return Version(f"{current.base_version}{kind}{number + 1}")
    if spec in ("next", "patch"):
        return Version(f"{current.major}.{current.minor}.{current.micro + 1}")
    if spec == "minor":
        return Version(f"{current.major}.{current.minor + 1}.0")
    if spec == "major":
        return Version(f"{current.major + 1}.0.0")
    return Version(spec)


def read_version(text: str, source: str) -> str:
    match = VERSION_RE.search(text)
    if match is None:
        raise SystemExit(f"error: no __version__ in {source}")
    return match.group(1)


def committed_version() -> Version:
    text = subprocess.run(
        ["git", "show", f"HEAD:{VERSION_FILES[-1]}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return Version(read_version(text, f"HEAD:{VERSION_FILES[-1]}"))


def write_version(version: Version) -> None:
    for name in VERSION_FILES:
        path = ROOT / name
        text, count = VERSION_RE.subn(f'__version__ = "{version}"', path.read_text())
        if count != 1:
            raise SystemExit(f"error: expected one __version__ in {name}")
        path.write_text(text)

    path = ROOT / CORE_PIN_FILE
    text, count = CORE_PIN_RE.subn(
        lambda match: f'"{match.group(1)}=={version}"', path.read_text()
    )
    if count != 1:
        raise SystemExit(f"error: expected one jupyter_ai_core pin in {CORE_PIN_FILE}")
    path.write_text(text)


def check() -> int:
    """
    Fail if the package versions and the jupyter_ai_core pin differ.
    """
    found = {
        name: read_version((ROOT / name).read_text(), name) for name in VERSION_FILES
    }
    pin = CORE_PIN_RE.search((ROOT / CORE_PIN_FILE).read_text())
    found[f"{CORE_PIN_FILE} (jupyter_ai_core pin)"] = pin.group(2) if pin else "missing"
    if len(set(found.values())) == 1:
        print(f"All packages are at version {found[VERSION_FILES[0]]}.")
        return 0
    print("error: the package versions are not in lockstep:", file=sys.stderr)
    for name, version in found.items():
        print(f"  {name}: {version}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "spec",
        nargs="?",
        help="new version, or one of: next, patch, minor, major",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="only check that the versions and the jupyter_ai_core pin agree",
    )
    args = parser.parse_args()

    if args.check:
        return check()
    if not args.spec:
        parser.error("a version spec is required")

    current = committed_version()
    version = increment(current, args.spec)
    write_version(version)
    print(f"Bumped {current} -> {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
