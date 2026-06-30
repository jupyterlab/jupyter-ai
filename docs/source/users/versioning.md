# Versioning and upgrading

Jupyter AI is built from many smaller subpackages (for example
`jupyter_ai_router`, `jupyter_ai_persona_manager`, and `jupyter_ai_tools`).
These subpackages follow [SemVer](https://semver.org/), and because this is a
fast-moving field, most are still on `0.x` versions, where we treat **every
minor release as potentially breaking**.

We apply the same convention to Jupyter AI itself:

- **Patch releases** (e.g. `3.0.0` → `3.0.1`) only raise dependency **floors**
  to require API-compatible patches of subpackages.
- **Minor releases** (e.g. `3.0.x` → `3.1.0`) raise dependency **ceilings** to
  introduce new features with API-breaking changes.

To keep subpackages from silently breaking installed environments, `jupyter_ai`
puts a **version ceiling** on each subpackage dependency that blocks its next
breaking version — for example `jupyter_ai_tools>=0.5.2,<0.6.0`. This lets
subpackages ship breaking changes on their own schedule without breaking your
`jupyter_ai` installation.

We currently do not have the bandwidth to support older versions of Jupyter AI.
We will only backport patches in exceptional circumstances (e.g. a major
security vulnerability), using community feedback as a reference point.

## For users

### Upgrade frequently

Because Jupyter AI moves fast, **we recommend upgrading as frequently as
possible** to pull in the latest changes. Most users should stay on the newest
release.

We recommend **not** upgrading with `pip` directly — its dependency solver is
not very good and may pull in incompatible versions. Prefer an environment
manager such as `conda`, `mamba`, `micromamba`, `uv`, or `pixi`.

````{tabs}

```{tab} micromamba (recommended)

    micromamba update -c conda-forge jupyter-ai

```

```{tab} uv

    uv pip install -U jupyter-ai

```

```{tab} venv / pip

    source .venv/bin/activate
    pip install -U jupyter-ai

```

````

### Chat files are not forwards-compatible

We do **not** promise that chat files are fully forwards-compatible — a chat
created in an older version of Jupyter AI may not work in a newer one. If you
need to carry context forward across an upgrade, we recommend asking an agent to
read the old chat file and summarize its context for re-use in a new chat.

## For extension developers

If you build an extension on top of Jupyter AI and import directly from one of
its subpackages, **add a version range around each specific subpackage whose
API you consume.** This prevents your environment solver from pulling in an
API-breaking release of that subpackage (as long as you are not using native
`pip`, whose solver does not enforce this reliably).

```toml
# your extension's pyproject.toml
dependencies = [
  "jupyter_ai_tools>=0.5.2,<0.6.0",  # or ==0.5.2 for an exact pin
]
```

Don't rely on the range that `jupyter_ai` declares — it exists to keep
`jupyter_ai` working, not to guarantee the specific API you import stays the
same. When you upgrade past a breaking boundary, review the subpackage's
changelog and update your pin after confirming your code still works.
