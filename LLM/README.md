# Guide for LLMs working on this repository

This directory contains information for an **LLM (large language model)** or AI assistant that is helping with the **enveloper** project. Use it to understand the repo, run checks, and follow conventions when making changes.

## What is enveloper?

**enveloper** is a Python package that manages environment secrets via the system keychain and cloud secret stores (AWS SSM, GitHub Secrets, GCP, Azure, Vault, etc.). It provides a CLI (`enveloper import/export/unexport`, etc.) and an optional SDK (`load_dotenv`, `dotenv_values`). Secrets are organized by **domain**, **project**, and **version** (semver). No `.env` files need to be committed.

- **Package name on PyPI:** `enveloper`
- **Repo:** [github.com/raminf/enveloper](https://github.com/raminf/enveloper) (this codebase may live under an `enveloper-py` subdirectory)

## Repository layout

| Path | Purpose |
|------|--------|
| `src/enveloper/` | Main package: CLI, stores, SDK, config, resolve_store. |
| `tests/` | Pytest tests; `tests/test_examples.py` for examples, `tests/conftest.py` for fixtures (mock keyring, sample_env). |
| `examples/` | Runnable examples: Docker, Makefile, Kubernetes, CI/CD, shell, GitHub Secrets, SDK, domains/versioning. Each has a README and optional script. |
| `docs/` | User-facing documentation (versioning, domains, SDK, CI/CD, etc.). |
| `docs-site/` | MkDocs site (Material theme); content comes from `docs/`. |
| `LLM/` | This folder: guidelines for LLMs. |
| `pyproject.toml` | Project config, dependencies, pytest markers, ruff/mypy. |

## Commands you should know

- **Install (development):** `uv sync --all-extras` or `make dev`
- **Run tests:** `uv run pytest tests/ -v` or `make test`
- **Run only unit (or integration) example tests:** `uv run pytest tests/test_examples.py -m unit` or `-m integration`
- **Lint:** `uv run ruff check src/ tests/` or `make lint`
- **Type-check:** `uv run mypy -p enveloper && uv run mypy tests/` or `make typecheck`
- **Full CI gate:** `make check` (lint + typecheck + test)

Use **uv** for running Python and installing dependencies (not pip or poetry).

## Guidelines (detailed)

Detailed guidelines for conventions, testing, and examples are in subdirectories:

| Document | Contents |
|----------|----------|
| [guidelines/conventions.md](guidelines/conventions.md) | Package manager (uv), Python version, project/domain semantics, code style. |
| [guidelines/testing.md](guidelines/testing.md) | How to run tests, pytest markers (unit/integration), conftest fixtures, adding tests. |
| [guidelines/examples.md](guidelines/examples.md) | How examples are structured, how to add a new example, documentation and tests. |
| [guidelines/mcp.md](guidelines/mcp.md) | MCP server: let other LLMs get a secret, list keys, export env, etc. from enveloper (human-friendly tools and messages). |

Read these when you need to add code, tests, or examples. For **exposing enveloper secrets to another LLM** (e.g. in Cursor), see [guidelines/mcp.md](guidelines/mcp.md) and [docs/mcp.md](../docs/mcp.md).

## After making changes

1. Run **`make check`** (or `make lint`, `make typecheck`, `make test` separately) to ensure nothing is broken.
2. If you add or change an example, ensure **`tests/test_examples.py`** still passes and add tests for new example content if appropriate.
3. If you change the LLM folder, run **`uv run pytest tests/test_llm.py -v`** to validate structure and required content.

## Documentation

Human-facing docs are in **`docs/`** and linked from the main **README.md**. The built site is at [enveloper.net](https://enveloper.net). There is a doc [docs/llm.md](../docs/llm.md) that points to this LLM folder for maintainers and LLMs.
