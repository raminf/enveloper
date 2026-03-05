# Conventions for LLMs

Conventions you should follow when editing this repository.

## Package manager: uv

- Use **uv** for installing and running. Do not use pip or poetry for project workflows.
- Examples: `uv run pytest tests/`, `uv run ruff check src/ tests/`, `uv sync --all-extras`, `uv add <package>` for new deps.
- The project may use a `Makefile` that wraps uv (e.g. `make test`, `make check`).

## Python version

- **Minimum Python:** 3.12 (see `requires-python` in `pyproject.toml`).
- Code can assume Python 3.12+ (e.g. `tomllib` in the standard library, no need for `tomli`).

## Project vs domain (enveloper semantics)

- **`--project` / `-p` / `ENVELOPER_PROJECT`** is an **internal namespace** for grouping secrets (e.g. `myapp`, `worker`). It is **not** the same as a cloud provider’s “project” (e.g. GCP project ID, AWS account). Do not conflate the two.
- **`--domain` / `-d` / `ENVELOPER_DOMAIN`** is a scope such as environment (`dev`, `prod`) or subsystem.
- **Defaults:** When omitted, domain and project resolve to `_default_` (or from env/config); version defaults to `1.0.0`. Defaults and key layout can differ across keychains and cloud providers.

## Code style and tooling

- **Ruff:** Linter and formatter; config in `pyproject.toml`. Avoid ambiguous names (e.g. variable `l` triggers E741).
- **Line length:** 130 (ruff).
- **Mypy:** Type-checking is used; some overrides exist for stores and CLI. Keep type hints where they help.

## Paths and layout

- Package source lives under **`src/enveloper/`**. Do not put package code in the repo root.
- Tests live in **`tests/`**; fixtures (e.g. `mock_keyring`, `sample_env`, `cli_runner`) are in **`tests/conftest.py`**.
- **Examples** live in **`examples/`** with one subfolder per example (e.g. `examples/docker/`, `examples/sdk/`); each should have a README and optional script. See [examples.md](examples.md).

## Secrets and safety

- Never commit real secrets. The repo uses a **sample.env** (or **examples/sample.env**) as a template; tests use mocks (e.g. in-memory keyring, file store with temp dirs) so no real keychain or cloud is touched in normal test runs.
