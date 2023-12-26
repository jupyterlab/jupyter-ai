#!/bin/bash

# script that bumps version for all projects regardless of whether they were
# changed since last release.

set -euxo pipefail
target_version="$1"

# bump version in pyproject.toml
# TODO

# we specify `--force-publish` because otherwise, `lerna version` only bumps
# versions for projects listed by `lerna changed`.
#
# see: https://github.com/lerna/lerna/issues/2369
(npx -p lerna@6.4.1 -y lerna version \
    --no-git-tag-version \
    --no-push \
    --force-publish \
    -y \
    "$target_version" \
) || exit 1
