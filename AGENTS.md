# AGENTS.md

Guidance for AI agents working in `jupyter-ai` and its subpackages.

## What Jupyter AI is

As of v3, `jupyter-ai` is **not a monorepo**. It is a metapackage that
distributes a working set of subpackages, each living in its own repo under the
[`jupyter-ai-contrib`](https://github.com/jupyter-ai-contrib) org. The
`jupyter-ai` repo itself is mostly empty; the composition is recorded in
`submodules/manifest.json` (a `"pypi_name": "org/repo"` map) and in the
[Contributor Guide](https://jupyter-ai.readthedocs.io/en/latest/contributors/index.html).

## Documentation lives with the code

Documentation is split by audience:

- **User docs** live solely in this repo, under `docs/source/users/`.
- **Contributor and developer docs live in each subpackage's own repo.** The
  main Jupyter AI docs site aggregates them into versioned subpages, so
  everything is readable in one place.

### If you are working in a subpackage repo

When you add or change functionality in a subpackage under `jupyter-ai-contrib/`,
put its contributor/developer documentation **in that subpackage's own repo**,
not here. Create either or both of:

```
docs/source/contributors/index.md   # → surfaces under Contributors on the main site
docs/source/developers/index.md     # → surfaces under Developers on the main site
```

- The `index.md` **H1 becomes the subpage title** — use the repo name by
  convention (e.g. `# jupyter-ai-tools`).
- The two sections are independent; define one, both, or neither.
- You may ship a **full subtree** (nested pages + images); your `index.md`'s
  `{toctree}` structures it.
- These pages flow up to https://jupyter-ai.readthedocs.io automatically once a
  maintainer bumps the doc submodule pins (see below). You do not edit the
  `jupyter-ai` repo to publish subpackage docs.

This is a **gradual rollout** — most subpackages do not have these docs yet, so
adding them is a genuine improvement, not a requirement to match existing repos.

### If you are working in this (`jupyter-ai`) repo

The submodule-docs aggregation infrastructure lives here:

- `submodules/manifest.json` — registry of doc submodules.
- `submodules/<repo>/` — git submodules, sparse-checked-out to `docs/` only.
- `scripts/update-doc-submodules.sh` — re-pins each submodule to the latest tag
  matching its `pyproject.toml` version range (PEP 440 via `packaging`). Run by
  the **Update submodule documentation** workflow (`workflow_dispatch`), which
  opens a PR with the new pins.
- `scripts/rtd-post-checkout.sh` — Read the Docs `post_checkout` hook that
  sparse-initialises the submodules.
- `docs/source/_ext/subpackage_docs.py` — Sphinx extension that copies each
  submodule's `docs/source/{contributors,developers}/` into git-ignored staging
  dirs and injects them into the aggregation toctrees. Missing docs are silently
  skipped; the build stays green.
- `docs/tests/` — integration tests (real `sphinx-build` against synthesized
  fixtures). The **Docs build system** CI workflow runs them on any change to
  the docs build system. Run them locally with `pytest docs/tests`.

When you add a new subpackage dependency that should contribute docs, add it to
`submodules/manifest.json` and run `scripts/update-doc-submodules.sh`.

## Writing release notes

Each release has a page under `docs/source/releases/<version>.md`. The title,
date, and per-subpackage changelog are auto-generated (wrapped in
`AUTO-GENERATED` markers — don't edit those). Your job as a contributor is the
**summary** in the `SUMMARY` markers: a human-readable overview that a reader
sees before the raw changelog. Edit only between the SUMMARY markers; a re-run of
the release-notes workflow regenerates everything else and preserves your
summary.

Write the summary for **users first**, developers second. Use these sections, in
order (drop any that don't apply):

- `## Highlights` — the handful of changes users will care about most.
- `## Major bugs fixed` — notable fixes, in plain "what was broken, now works"
  terms.
- `## API changes` — for extension developers: what they can now build, and the
  methods they'd implement.
- Optional `:::{note}` admonitions for caveats or forward-looking context.
- The auto-generated per-subpackage changelog follows as the full changelog.

### Style, learned from real edits

**Lead with what a change *does*, not how it's built.** Implementation details
(transport, internal wiring) are noise in a summary.

> Before: "Persona session state now flows over a Yjs awareness channel instead
> of REST, and message routing is driven by per-message metadata rather than
> `@`-mentions. The old active-persona REST endpoints are removed."
>
> After: "The APIs powering the new in-chat controls are all built into the
> Persona API, so any persona can advertise its models, settings, and session
> usage and reuse the built-in chat UI — no custom REST API required."

**Be precise about what's actually new vs. moved.** Don't call something
"upstreamed" if it never existed before; reserve that for APIs genuinely moved
out of a specific package. (E.g. the `report_*`/`update_*` methods are new this
release; only `cancel_response()` was moved out of the ACP client into the base
Persona API.)

**In `## API changes`, list the methods a developer implements** — real method
name, empty-argument-shape signature, one sentence each. Skip methods that are
only *called* for you (plumbing/implementation details).

> Before: "`BasePersona` gains `get_*` accessors, `report_*` publishers, and
> `apply_model_spec` / `apply_settings_spec` appliers."
>
> After:
> - `report_model_configuration(model)` — advertise the current model and its
>   options, populating the model picker.
> - `report_usage(usage)` — publish context-window, token, and cost usage for
>   the live gauge.
> - `update_model(model_id)` — switch the persona to the selected model.
>
> (Dropped `get_*` readers and `apply_*_spec` — those are read by/called for the
> persona, not implemented by it.)

**Drop parentheticals in Highlights.** They read as hedging; fold the detail
into the sentence or cut it.

> Before: "works with JupyterLab 4.6+ (Jupyter YDoc v4)" ·
> "switch its model, mode, and options (reasoning effort, permissions, and more)"
>
> After: "works with JupyterLab 4.6+" ·
> "switch the active agent's model, permission mode, effort, and other settings"

**Use user-facing product language.** Name things as a user sees them, not as
the code does.

> Before: "A new control row lets you pick which persona replies"
>
> After: "A new input toolbar lets you pick which persona replies"

**Admonitions use colon-fences, not backtick-fences**, so Sphinx renders a note
while plain-Markdown previews (GitHub, etc.) show prose instead of a code block:

````
:::{note}
The permission-requests API remains the only API specific to ACP agents.
:::
````

## Building and testing docs locally

```
pip install -r docs/requirements.txt
sphinx-build -b html docs/source docs/_build/html
pytest docs/tests          # aggregation integration tests
```

See the [Contributor Guide](https://jupyter-ai.readthedocs.io/en/latest/contributors/index.html)
for the full development setup, the devrepo workflow, and design principles.
