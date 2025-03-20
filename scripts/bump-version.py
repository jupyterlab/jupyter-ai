# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

"""
The "bump version" script used by Jupyter Releaser to increment the version of
Jupyter AI on manual release workflow runs. This script:

- Accepts a *specified version* `spec_version` as the first positional argument.
`spec_version` must be either a PEP-440 version string or "minor" literally.

    - Normal release version examples: "0.1.0", "1.2.3", "3.0.0"

    - Pre-release version examples: "3.0.0a0", "3.0.0b1", "3.0.0rc2"

    - **NOTE**: This script was not designed to support dev & post-releases for
    simplicity. By convention, our repo prefers patch releases over
    post-releases and pre-releases over dev releases.

- Bumps `jupyter-ai` and `jupyter-ai-magics` to `spec_version`. If
`spec_version` is "minor", then this script bumps the minor version of each
package.

- Updates `jupyter-ai`'s required version of `jupyter-ai-magics` to exactly
match the specified version. In other words, this script ensures
`jupyter-ai==x.y.z` always depends on `jupyter-ai-magics==x.y.z` exactly.

- If `--skip-if-dirty` is passed, successive calls do nothing. This is a
temporary workaround for
https://github.com/jupyter-server/jupyter_releaser/issues/567.
"""

from pathlib import Path

import click
import tomlkit
from jupyter_releaser.util import get_version, run
from packaging.version import Version
from pkg_resources import parse_version

MONOREPO_ROOT = Path(__file__).parent.parent.resolve()
LERNA_CMD = "npx -p lerna@6.4.1 -y lerna version --no-push --force-publish --no-git-tag-version -y"


@click.command()
@click.option("--ignore-dirty", default=False, is_flag=True)
@click.option("--skip-if-dirty", default=False, is_flag=True)
@click.argument("spec", nargs=1)
def bump_version(ignore_dirty: bool, skip_if_dirty: bool, spec: str):
    is_dirty = len(run("git status --porcelain").strip()) > 0
    if is_dirty and not ignore_dirty:
        if skip_if_dirty:
            print(
                "Skipping this call as the repo is in a dirty state with untracked files."
            )
            return
        raise Exception("Must be in a clean git state with no untracked files")

    next_version: Version = compute_next_version(spec)

    # convert the PyPI version string to a NPM version string
    next_version_npm = f"{next_version.major}.{next_version.minor}.{next_version.micro}"
    if next_version.pre:
        pre_type, pre_number = next_version.pre
        if pre_type == "a":
            pre_type = "alpha"
        elif pre_type == "b":
            pre_type = "beta"
        elif pre_type == "rc":
            pre_type = "rc"
        else:
            raise Exception(f"Unrecognized pre-release type: '{pre_type}'.")
        next_version_npm += f"-{pre_type}.{pre_number}"

    # bump the versions in NPM packages
    #
    # Note: `_version.py` files do not need to be updated manually.
    # `hatch-nodejs-version` updates those files automatically on build, setting
    # them to the version specified in the corresponding package.json file.
    lerna_cmd = f"{LERNA_CMD} {next_version_npm}"
    run(lerna_cmd)

    # bump the version of `jupyter-ai-magics` required by `jupyter-ai`
    jai_pyproject_path = MONOREPO_ROOT / "packages" / "jupyter-ai" / "pyproject.toml"
    jai_pyproject = tomlkit.parse(jai_pyproject_path.read_text())
    jai_deps = jai_pyproject.get("project").get("dependencies")
    for i, dep in enumerate(jai_deps):
        if str(dep).startswith("jupyter_ai_magics"):
            next_major_version = f"{next_version.major + 1}.0.0"
            jai_deps[i] = (
                f"jupyter_ai_magics>={str(next_version)},<{next_major_version}"
            )
            break

    # write updated pyproject.toml file
    jai_pyproject_path.write_text(tomlkit.dumps(jai_pyproject))


def compute_next_version(spec: str) -> Version:
    if spec == "minor":
        curr_version = parse_version(get_version())
        next_version = parse_version(
            f"{curr_version.major}.{curr_version.minor + 1}.{curr_version.micro}"
        )
    else:
        next_version = parse_version(spec)

    return next_version


if __name__ == "__main__":
    bump_version()
