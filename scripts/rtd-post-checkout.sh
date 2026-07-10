#!/usr/bin/env bash
#
# rtd-post-checkout.sh
#
# Read the Docs `build.jobs.post_checkout` hook. This is the single owner of
# documentation-submodule initialisation on the RTD side.
#
# Read the Docs' native `submodules:` support performs a full checkout of each
# submodule, which cannot do a sparse checkout. Our submodules are large
# subpackage repos and we only want each one's `docs/` directory, so we drive
# the submodule checkout ourselves here instead of setting a `submodules:` key
# in `.readthedocs.yaml`.
#
# For every submodule registered in `.gitmodules`, this:
#   1. initialises the submodule config,
#   2. enables no-cone sparse checkout limited to `docs/`, and
#   3. checks the submodule out at its pinned commit.
#
# All submodules are public repos on GitHub, so they are cloned over anonymous
# HTTPS (the URLs in `.gitmodules`); no token or auth is required.
#
# A subpackage that has not cut any docs yet simply yields an empty working
# tree — that is expected during the gradual rollout and is not an error.

set -euo pipefail

# RTD runs this from the repo root, but be explicit so a local dry-run works
# from anywhere.
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [[ ! -f .gitmodules ]]; then
  echo "[post_checkout] no .gitmodules; nothing to do"
  exit 0
fi

# Iterate submodule paths from .gitmodules.
paths="$(git config --file .gitmodules --get-regexp '^submodule\..*\.path$' | awk '{print $2}')"

for path in $paths; do
  echo "[post_checkout] initialising $path (sparse: docs/)"

  # Register the submodule's URL/config without fetching content yet.
  git submodule init "$path"

  # Enable sparse checkout limited to docs/ *before* fetching the work tree, so
  # only docs/ is ever materialised.
  git submodule update --init --no-fetch "$path" 2>/dev/null || true
  git -C "$path" config core.sparseCheckout true
  git -C "$path" sparse-checkout init --no-cone 2>/dev/null || true
  git -C "$path" sparse-checkout set --no-cone docs

  # Fetch and check out the pinned commit for this submodule.
  git submodule update --init "$path"

  # Re-apply the sparse pattern now that the tree is populated, then prune
  # anything outside docs/ that a full checkout may have written.
  git -C "$path" sparse-checkout reapply 2>/dev/null || true
done

echo "[post_checkout] done"
