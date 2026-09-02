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
ranges point at those new subpackage versions.

The version-range model is what keeps this manageable, and it is worth reading
{doc}`Versioning and upgrading </users/versioning>` before a release:

- **None of the subpackages put version ceilings on each other.** A subpackage
  can require `>=` a floor of another subpackage, but never caps it. This is why
  publishing an official patch of a subpackage automatically reaches existing
  installs.
- **Only the `jupyter-ai` metapackage enforces version ceilings** on its
  subpackage dependencies (for example `jupyter_ai_tools>=0.5.2,<0.6.0`). These
  ceilings are bumped each minor release, which is how a subpackage's breaking
  changes reach users.

```{note}
Because subpackages have no ceilings on each other, an official **patch** of a
subpackage updates new installs on its own. A matching patch release of
`jupyter-ai` itself is **not strictly necessary**; we mainly cut one to
communicate that bug fixes or security fixes shipped. Informally this happens
each Monday if there are new patches.
```

The order of operations for an official release is:

1. [Release all subpackages](#step-1-release-the-subpackages)
2. [Bump subpackage version ranges in `jupyter-ai` and merge](#step-2-bump-version-ranges)
3. [Run "Step 0: Prep release documentation"](#step-3-prep-release-documentation-step-0)
4. [Edit the generated changelog in the PR that Step 0 opens](#step-4-edit-and-merge-the-changelog)
5. [Merge the changelog PR](#step-4-edit-and-merge-the-changelog)
6. [Run "Step 1" and "Step 2" to publish `jupyter-ai`](#step-5-publish-jupyter-ai-steps-1-and-2)

Releasing on conda-forge is a separate, downstream process covered
[at the end of this page](#releasing-on-conda-forge). Common one-off questions
are answered in the [FAQ](#faq).

(step-1-release-the-subpackages)=
## 1. Release the subpackages

Every Jupyter AI subpackage (for example `jupyter-ai-persona-manager`,
`jupyter-ai-router`, `jupyter-ai-tools`) uses
[Jupyter Releaser](https://jupyter-releaser.readthedocs.io/). Releasing one is
as simple as running its two manual GitHub Actions workflows in order:

- **Step 1: Prep Release** builds the changelog and opens a release PR.
- **Step 2: Publish Release** publishes the release to PyPI (and npm, where
  applicable) and creates the GitHub release.

```{important}
When running Step 1 for any **official** release, check the "use PRs since the
last stable tag" option (`since_last_stable`) so the changelog covers everything
since the last stable release rather than since the last pre-release. Leave it
**unchecked only for pre-releases**.
```

### Release ordering

- **Independent upgrade** (the subpackage does not require a new version of any
  other subpackage): just release it. No ordering needed.
- **Dependent upgrade** (for example a change to `jupyter-ai-router` that
  `jupyter-ai-persona-manager` must then adopt): release in **topological
  order**. Release `jupyter-ai-router` first, then bump
  `jupyter-ai-persona-manager`'s floor on it and release that, and so on up the
  dependency chain.

```{note}
When bumping one subpackage's dependency on another, update **both**
`pyproject.toml` and `package.json` (if the subpackage ships a JavaScript
package). A floor bumped in only one of the two will pass CI but ship an
inconsistent dependency set.
```

(step-2-bump-version-ranges)=
## 2. Bump subpackage version ranges

Once the subpackages are published, bump their version ranges in the
`jupyter-ai` metapackage so it points at the newly released versions.

- Update the subpackage dependency ranges in `pyproject.toml`.
- Open a PR with the range bumps and merge it into the target branch.

Which end of the range you bump depends on the release type (see
{doc}`Versioning and upgrading </users/versioning>`):

- **Patch release** (e.g. `3.0.0` → `3.0.1`): bump the **floor** only, to require
  API-compatible patches of subpackages.
- **Minor release** (e.g. `3.0.x` → `3.1.0`): bump the **floor and the ceiling**,
  to pull in subpackages' new (potentially breaking) features.

```{note}
The ranges must be bumped in the target branch **before** Step 0 runs. The
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

With the ranges bumped and the changelog merged, release `jupyter-ai` itself
using the same Jupyter Releaser workflows the subpackages use:

- **Step 1: Prep Release** (`prep-release.yml`)
- **Step 2: Publish Release** (`publish-release.yml`)

As with the subpackages, check the "use PRs since the last stable tag"
(`since_last_stable`) option in Step 1 for an official release, and leave it
unchecked only for a pre-release.

```{seealso}
The repo's [`AGENTS.md`](https://github.com/jupyterlab/jupyter-ai/blob/main/AGENTS.md)
documents the release tooling in more detail (including the "Writing release
notes" workflow and the `scripts/generate_release_notes.py` script behind
Step 0), and is the reference for agents driving a release.
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

(faq)=
## FAQ

### How do I publish a pre-release?

Use [PyPI pre-release version syntax](https://packaging.python.org/en/latest/specifications/version-specifiers/#pre-releases)
for the version specifier: `0.2.0a0` (alpha), `0.2.0b0` (beta), or `0.2.0rc0`
(release candidate) instead of `0.2.0`. For a pre-release, leave the "use PRs
since the last stable tag" (`since_last_stable`) option **unchecked** in Step 1.

### How do I update the release notes generated by Step 0?

Re-run the "Step 0: Prep release documentation" workflow. It is safe to run
again even if the notes were already generated: each run merges the target
branch back into the release-docs branch, so re-running after merging the
version-range bump into `main` picks up the new updates.
