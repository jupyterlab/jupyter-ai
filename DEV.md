# Developer Guide

This document explains how to set up a local development environment, run
tests, run the linter, and use the AI repo-testing tooling shipped with this
repository.

---

## Table of contents

1. [Prerequisites](#prerequisites)
2. [Local setup](#local-setup)
3. [Running tests](#running-tests)
4. [Running lint / format checks](#running-lint--format-checks)
5. [AI repo testing](#ai-repo-testing)
   - [Running locally](#running-locally)
   - [CI integration](#ci-integration)
   - [Enabling repositories (allowlist)](#enabling-repositories-allowlist)
   - [Safety constraints](#safety-constraints)

---

## Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Python | 3.9 | 3.11 recommended |
| pip | 23+ | bundled with Python ≥ 3.12 |
| git | 2.30+ | |

Optional (for full JS build):

| Tool | Notes |
|------|-------|
| Node.js 18+ | Required only if you need to rebuild front-end assets |
| yarn / jlpm | `jlpm` ships with JupyterLab |

---

## Local setup

```bash
# 1. Clone the repository
git clone https://github.com/rpreslar4765/jupyter-ai.git
cd jupyter-ai

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install the package with development / test extras
pip install -e ".[test]"

# 4. (Optional) Install pre-commit hooks
pip install pre-commit
pre-commit install
```

> **Conda / Micromamba users:** You can use `scripts/dev-setup.sh` which
> creates a `jaidev` conda environment automatically.

---

## Running tests

```bash
# Run all unit tests
pytest

# Run with coverage
pytest --cov=jupyter_ai --cov-report=term-missing

# Run a specific test file
pytest path/to/test_something.py -v
```

Tests are discovered automatically via `conftest.py` in the repository root.

---

## Running lint / format checks

This repository uses [pre-commit](https://pre-commit.com/) to manage linting
and formatting hooks:

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run a single hook
pre-commit run black --all-files
pre-commit run isort --all-files
pre-commit run flake8 --all-files --hook-stage manual
```

Hooks configured in `.pre-commit-config.yaml`:

| Hook | Purpose |
|------|---------|
| `black` | Code formatter |
| `isort` | Import sorter |
| `autoflake` | Remove unused imports |
| `pyupgrade` | Upgrade Python syntax |
| `flake8` | Style / bug linter (manual stage) |
| `end-of-file-fixer` | Ensure files end with newline |
| `trailing-whitespace` | Remove trailing whitespace |

---

## AI repo testing

The `scripts/ai_repo_tester.py` script uses the GitHub API to enumerate
repositories owned by a given user, clone each one, run CI-equivalent checks,
and produce a JSON report plus a Markdown summary.

### Running locally

```bash
# Install dependencies
pip install PyGithub requests

# Export a GitHub PAT (needs `repo` scope for private repos; `public_repo` for public)
export GITHUB_TOKEN=ghp_...

# Dry run – no PRs opened
python scripts/ai_repo_tester.py \
    --user rpreslar4765 \
    --dry-run \
    --output-dir /tmp/ai-reports \
    --allowlist scripts/ai_testing_allowlist.txt

# Open up to 2 fix PRs on allowlisted repos
python scripts/ai_repo_tester.py \
    --user rpreslar4765 \
    --max-prs 2 \
    --output-dir /tmp/ai-reports \
    --allowlist scripts/ai_testing_allowlist.txt
```

Output files written to `--output-dir`:

| File | Description |
|------|-------------|
| `report.json` | Machine-readable full report |
| `summary.md` | Human-readable Markdown table |

### CI integration

The workflow `.github/workflows/ai-repo-testing.yml` runs:

- **Scheduled:** daily at 06:00 UTC.
- **Manual dispatch:** via the *Actions* → *AI Repo Testing* → *Run workflow*
  button in GitHub. Inputs:
  - `target_user` – GitHub username to scan (default: `rpreslar4765`).
  - `max_prs` – maximum fix PRs to open (default: `3`).
  - `dry_run` – set to `false` to actually open PRs (default: `true`).

Report artifacts are uploaded as workflow artifacts and the Markdown summary
is appended to the GitHub Actions job summary.

### Enabling repositories (allowlist)

To allow the tester to open automated fix PRs on a repository, add its full
name (`owner/repo`) to `scripts/ai_testing_allowlist.txt`:

```
# scripts/ai_testing_allowlist.txt
rpreslar4765/jupyter-ai
rpreslar4765/some-other-repo
```

Repositories **not** in the allowlist will still be tested and appear in the
report, but no PR will be opened on them.

### Safety constraints

| Constraint | Value |
|-----------|-------|
| Allowlist required | Yes – PRs only on listed repos |
| Max PRs per run | Configurable (`--max-prs`, default 3) |
| Auto-merge | **Never** |
| Write token scope | `GITHUB_TOKEN` (scoped to the workflow run) |
| Fork safety | Workflow uses `pull_request` trigger, not `pull_request_target` |
| Dry run | Default `true` in scheduled runs |

To add new check types or fix templates, edit `scripts/ai_repo_tester.py` and
update the `_PR_FIXES` mapping.
