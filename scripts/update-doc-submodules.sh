#!/usr/bin/env bash
#
# update-doc-submodules.sh
#
# Pins every documentation submodule listed in submodules/manifest.json to the
# latest git tag that satisfies the corresponding package's version range in
# jupyter-ai's pyproject.toml, and sparse-checks-out each submodule to docs/.
#
# This is the single source of truth for submodule pinning. It is run:
#   * once, to seed the submodules in the infrastructure PR, and
#   * on demand via the "Update submodule documentation" GitHub workflow
#     (workflow_dispatch), which runs it and opens a PR with the result.
#
# Version resolution follows pip / PEP 440 semantics via the `packaging`
# library (SpecifierSet.filter), so pre-releases are excluded for a stable
# range like ">=0.6.0,<0.7.0" but included for a pre-release range like
# ">=0.23.0a2,<0.24". Tags across the jupyter-ai-contrib repos are uniformly
# "v"-prefixed PEP 440 versions (e.g. v0.6.0, v0.2.0b0); the leading "v" is
# stripped before parsing.
#
# A submodule whose range matches no published tag (e.g. a package that has
# not cut a release yet) is pinned to its default branch HEAD instead, and a
# warning is emitted. The build still succeeds; docs simply track the tip until
# a matching tag exists.
#
# Requirements: git, python3 with the `packaging` library (and `tomllib` on
# Python 3.11+, or `tomli` on 3.10). All of these are available in the docs /
# CI environment.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MANIFEST="submodules/manifest.json"
PYPROJECT="pyproject.toml"

if [[ ! -f "$MANIFEST" ]]; then
  echo "error: $MANIFEST not found (run from a jupyter-ai checkout)" >&2
  exit 1
fi

# Resolve the pin plan in Python: for each manifest entry, read the package's
# range from pyproject.toml, list the remote's tags, and pick the winning ref.
# Emits one tab-separated row per submodule: path <TAB> url <TAB> ref <TAB> kind
# where kind is "tag" or "branch". Human-readable progress goes to stderr.
PLAN="$(python3 scripts/_resolve_doc_submodules.py "$MANIFEST" "$PYPROJECT")"

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
