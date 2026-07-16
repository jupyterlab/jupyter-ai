#!/usr/bin/env bash
#
# update-doc-submodules.sh [--mode main|release]
#
# Pins every documentation submodule listed in submodules/manifest.json and
# sparse-checks-out each to docs/. Has two modes (see
# scripts/_resolve_doc_submodules.py for the full rationale):
#
#   --mode main (default)
#       Pin every submodule to its default-branch HEAD. Used by the routine
#       "update submodule documentation" workflow so the `latest` docs (built
#       from jupyter-ai's main) always show each subpackage's newest docs — no
#       subpackage release required.
#
#   --mode release
#       Pin each submodule to the latest tag matching that package's version
#       range in pyproject.toml (pip / PEP 440 semantics). Used by the release
#       hook (see scripts/freeze-doc-submodules.sh) so a jupyter-ai release tag
#       captures a coherent, frozen snapshot of the subpackage docs.
#
# This is the single source of truth for submodule pinning; it also seeded the
# submodules originally.
#
# Requirements: git, python3 with the `packaging` library (and `tomllib` on
# Python 3.11+, or `tomli` on 3.10). All of these are available in the docs /
# CI environment.

set -euo pipefail

MODE="main"
if [[ "${1:-}" == "--mode" ]]; then
  MODE="${2:-main}"
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MANIFEST="submodules/manifest.json"
PYPROJECT="pyproject.toml"

if [[ ! -f "$MANIFEST" ]]; then
  echo "error: $MANIFEST not found (run from a jupyter-ai checkout)" >&2
  exit 1
fi

# Resolve the pin plan in Python. Emits one tab-separated row per submodule:
# path <TAB> url <TAB> ref <TAB> kind  (kind is "tag" or "branch"). Human-
# readable progress goes to stderr.
PLAN="$(python3 scripts/_resolve_doc_submodules.py "$MANIFEST" "$PYPROJECT" --mode "$MODE")"

if [[ -z "$PLAN" ]]; then
  echo "error: resolver produced no plan" >&2
  exit 1
fi

# Iterate the plan and pin each submodule.
while IFS=$'\t' read -r path url ref kind; do
  [[ -z "$path" ]] && continue
  echo "==> $path -> $ref ($kind)"

  # Register the submodule if it is not already in .gitmodules.
  if ! git config -f .gitmodules --get "submodule.$path.url" >/dev/null 2>&1; then
    # `--force` lets us re-add a path whose directory already exists on disk.
    git submodule add --force "$url" "$path" >/dev/null 2>&1 || {
      echo "error: failed to add submodule $path" >&2
      exit 1
    }
  fi

  # Ensure the submodule is initialised and sparse-checked-out to docs/ only.
  git submodule update --init "$path" >/dev/null 2>&1 || true
  git -C "$path" sparse-checkout init --no-cone >/dev/null 2>&1 || true
  git -C "$path" sparse-checkout set --no-cone docs >/dev/null 2>&1 || true

  # Fetch tags and the resolved ref, then detach onto it.
  git -C "$path" fetch --quiet --tags origin || true
  if [[ "$kind" == "tag" ]]; then
    checkout_ref="refs/tags/$ref"
  else
    git -C "$path" fetch --quiet origin "$ref" || true
    checkout_ref="FETCH_HEAD"
  fi
  git -C "$path" checkout --quiet --detach "$checkout_ref"

  # Stage the moved gitlink (and .gitmodules on first registration).
  git add "$path" .gitmodules
done <<< "$PLAN"

echo
echo "Done. Staged submodule pins:"
git submodule status || true
