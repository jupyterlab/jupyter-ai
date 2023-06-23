#!/bin/bash

# script that bumps version for all projects regardless of whether they were
# changed since last release. needed because `lerna version` only bumps versions for projects
# listed by `lerna changed` by default.
#
# see: https://github.com/lerna/lerna/issues/2369

(npx -p lerna@6.4.1 -y lerna version \
    --no-git-tag-version \
    --no-push \
    --force-publish \
    -y \
    $1 \
) || exit 1
