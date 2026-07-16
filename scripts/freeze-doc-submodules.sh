#!/usr/bin/env bash
#
# freeze-doc-submodules.sh
#
# Release-time hook: pin every documentation submodule to the released tag that
# matches its version range in pyproject.toml, and stage the moved gitlinks.
#
# Between releases the doc submodules track each subpackage's `main` (so the
# `latest` docs show the freshest, possibly-unreleased subpackage docs). At
# release time we want the opposite: the release tag should capture a coherent,
# *frozen* snapshot of the subpackage docs that ship with this jupyter-ai
# version. This script performs that freeze by delegating to
# `update-doc-submodules.sh --mode release`.
#
# It is wired as a jupyter-releaser `after-bump-version` hook (see
# [tool.jupyter-releaser.hooks] in pyproject.toml): during "Step 1: Prep
# Release" the releaser bumps the version, runs this hook, then commits the
# working tree (including the re-pinned gitlinks staged here) and tags it. So
# the release tag — and therefore the `stable` docs Read the Docs serves — gets
# the frozen pins, while `main` keeps tracking the subpackage `main` branches.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "Freezing documentation submodules to release tags for this version…"
bash scripts/update-doc-submodules.sh --mode release

# update-doc-submodules.sh already `git add`s the moved gitlinks and
# .gitmodules; jupyter-releaser's changelog/commit step sweeps them into the
# release commit. Nothing else to do here.
echo "Documentation submodules frozen and staged."
