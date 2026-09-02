# Release Process

This page documents how maintainers cut an official release of Jupyter AI.

```{note}
This is a high-level scaffold. Each section captures the overall shape of the
process; step-by-step commands, screenshots, and edge cases still need to be
filled in.
```

## Audience

This guide is for Jupyter AI **maintainers** with release permissions on the
[`jupyterlab/jupyter-ai`](https://github.com/jupyterlab/jupyter-ai) repo and the
subpackage repos under the
[`jupyter-ai-contrib`](https://github.com/jupyter-ai-contrib) org.

## Overview

In v3, Jupyter AI is a metapackage that pins a working set of independently
released subpackages. A full release therefore happens in two layers: first the
subpackages are released, then `jupyter-ai` itself is released once its version
floors point at those new subpackage versions.

The order of operations for an official release is:

1. [Release all subpackages](#step-1-release-the-subpackages)
2. [Bump version floors in `jupyter-ai` and merge](#step-2-bump-version-floors)
3. [Run "Step 0: Prep release documentation"](#step-3-prep-release-documentation-step-0)
4. [Edit the generated changelog in the PR that Step 0 opens](#step-4-edit-and-merge-the-changelog)
5. [Merge the changelog PR](#step-4-edit-and-merge-the-changelog)
6. [Run "Step 1" and "Step 2" to publish `jupyter-ai`](#step-5-publish-jupyter-ai-steps-1-and-2)

Releasing on conda-forge is a separate, downstream process covered
[at the end of this page](#releasing-on-conda-forge).

(step-1-release-the-subpackages)=
## 1. Release the subpackages

Every Jupyter AI subpackage (for example `jupyter-ai-persona-manager`,
`jupyter-ai-router`, `jupyter-ai-tools`) uses
[Jupyter Releaser](https://jupyter-releaser.readthedocs.io/). Releasing one is
as simple as running its two manual GitHub Actions workflows in order:

- **Step 1: Prep Release** builds the changelog and opens a release PR.
- **Step 2: Publish Release** publishes the release to PyPI (and npm, where
  applicable) and creates the GitHub release.

```{note}
TODO: document how to decide which subpackages need a new release, and any
ordering constraints between subpackages that depend on one another.
```

(step-2-bump-version-floors)=
## 2. Bump version floors

Once the subpackages are published, bump their version floors in the
`jupyter-ai` metapackage so it pins the newly released versions.

- Update the dependency floors in `pyproject.toml`.
- Open a PR with the floor bumps and merge it into the target branch.

```{note}
The floors must be bumped in the target branch **before** Step 0 runs. The
release-notes generator reads each subpackage's floor from `pyproject.toml` to
compute the PR window for that subpackage.
```

(step-3-prep-release-documentation-step-0)=
## 3. Prep release documentation (Step 0)

Run the **"Step 0: Prep release documentation"** workflow
(`prep-release-docs.yml`) on `jupyterlab/jupyter-ai`.

This workflow generates the docs "Releases" page for the new version and opens
it as a draft PR against the target branch. The docs
{doc}`Releases </releases/index>` section, not Jupyter Releaser's changelog and
not the GitHub release, is the source of truth for Jupyter AI release notes.

Inputs:

- **version**: the new version being released, for example `v3.2.0`.
- **target-branch**: the branch to target (`main` by default; patch releases of
  older minors are cut from maintenance branches such as `3.0.x`).

Under the hood it reuses Jupyter Releaser's changelog builder to aggregate PRs
and contributors across every submodule, resolving each submodule's PR window
from its version floors at the previous release versus this release.

(step-4-edit-and-merge-the-changelog)=
## 4. Edit and merge the changelog

The draft PR opened by Step 0 contains the auto-generated release notes page
(for example `docs/source/releases/v3.2.0.md`).

- Review and edit the generated changelog for accuracy and readability.
- Merge the changelog PR into the target branch.

```{note}
TODO: document the editorial conventions for the changelog (highlights,
grouping, what to trim from the auto-generated list).
```

(step-5-publish-jupyter-ai-steps-1-and-2)=
## 5. Publish `jupyter-ai` (Steps 1 and 2)

With the floors bumped and the changelog merged, release `jupyter-ai` itself
using the same Jupyter Releaser workflows the subpackages use:

- **Step 1: Prep Release** (`prep-release.yml`)
- **Step 2: Publish Release** (`publish-release.yml`)

```{note}
TODO: document the input values typically used for Step 1 (version specifier,
target branch, `since_last_stable`) and any post-publish verification.
```

(releasing-on-conda-forge)=
## Releasing on conda-forge

Publishing the release to [conda-forge](https://conda-forge.org/) is a separate,
downstream process. Unlike the PyPI release above, it is **not** automated by a
single workflow and requires familiarity with conda-forge feedstocks: you edit a
feedstock's `recipe/meta.yaml` (or v1 `recipe.yaml`), update the version and
source hash, rerender with `conda-smithy`, and open a PR against the feedstock.

At a high level:

1. Each Jupyter AI package has its own feedstock under the
   [conda-forge](https://github.com/conda-forge) org (for example
   `jupyter-ai-feedstock`).
2. For each package, open a version-bump PR on its feedstock that updates the
   version and sha256, resets the build number, and rerenders with the latest
   `conda-smithy`.
3. Merge feedstock PRs in dependency order so each package's run requirements
   resolve against versions already available on the channel.

```{note}
Pre-releases use the CFEP-05 `rc`/`dev` branch workflow with dedicated channel
labels, which adds further steps. Do not attempt a conda-forge release without
understanding the feedstock and channel model.
```

```{seealso}
The [`conda-forge-skills`](https://github.com/dlqqq/conda-forge-skills)
repository collects agent skills that automate much of this feedstock work,
including
[`create-recipe`](https://github.com/dlqqq/conda-forge-skills/blob/main/skills/create-recipe),
[`create-prerelease-branches`](https://github.com/dlqqq/conda-forge-skills/blob/main/skills/create-prerelease-branches),
and
[`open-feedstock-pr`](https://github.com/dlqqq/conda-forge-skills/blob/main/skills/open-feedstock-pr).
```
