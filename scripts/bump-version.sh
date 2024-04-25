#!/bin/bash

# Script used by Jupyter Releaser that bumps the version of all packages to the
# one provided in `$1`. This script requires `jq` to be installed.
#
# This script is necessary because a) `lerna version` only bumps versions for
# projects listed by `lerna changed` by default [1], and b) the version in
# `packages/jupyter-ai/pyproject.toml` needs to be bumped as well.
#
# [1]: https://github.com/lerna/lerna/issues/2369

(npx -p lerna@6.4.1 -y lerna version \
    --no-git-tag-version \
    --no-push \
    --force-publish \
    -y \
    "$1" \
) || exit 1

if [[ "$PWD" == *packages/jupyter-ai ]]; then
    version=$(cat package.json | jq -r '.version')
    # bump dependency in jupyter-ai to rely on current version of jupyter-ai-magics
    # -E : use extended regex to allow usage of `+` symbol
    # -i.bak : edit file in-place, generating a backup file ending in `.bak`, which we delete on success
    #          while confusing, this unfortunately is the only way to edit in-place on both macOS and Linux
    #          reference: https://stackoverflow.com/a/44864004
    sed -E -i.bak "s/jupyter_ai_magics.=[0-9]+\.[0-9]+\.[0-9]+/jupyter_ai_magics==$version/" pyproject.toml && rm pyproject.toml.bak
fi
