# Enveloper usage examples

This folder contains runnable examples showing how to use [enveloper](https://pypi.org/project/enveloper/) so that **secrets stay out of `.env` files** and are loaded from the system keychain or a cloud secret store (e.g. AWS SSM) at runtime.

## Concepts

- **`import`** — Load variables from a file (e.g. `sample.env`) into the keychain or cloud store. Use this once to populate the store; no need to keep a `.env` in the repo.
- **`export --format unix`** — Emit shell commands that set environment variables. Use with `eval` to load those values into the current process.
- **`unexport --format unix`** — Emit shell commands that unset those variables. Use with `eval` to clear them from the environment when done.

All examples use the same **domain** and **project** as the [sample.env](sample.env) comments: `--domain mydomain --project myproject` (or `-d mydomain -p myproject`). You can change these to match your own naming.

## Prerequisites

1. Install enveloper (from PyPI). For **CLI-only** use (scripts, Make, Docker, CI):

   ```bash
   pip install enveloper
   # With a cloud backend, e.g. AWS:
   pip install enveloper[aws]
   ```

   For **Python apps** that load secrets at runtime (keychain or cloud), install the **SDK** extra:

   ```bash
   pip install enveloper[sdk]
   # Or CLI + SDK + cloud backends:
   pip install enveloper[all]
   ```

2. (Optional) Import the example env into your keychain so the examples have something to read:

   ```bash
   enveloper import sample.env --domain mydomain --project myproject
   ```

   Or pull from a cloud store if you already pushed there:

   ```bash
   enveloper pull --service aws --domain mydomain --project myproject
   ```

## Example index

| Example | Description |
|--------|-------------|
| [docker/](docker/) | Run a container that loads secrets from keychain or AWS (no `.env` file). |
| [makefile/](makefile/) | Use enveloper in a Makefile: load env for targets, then unexport when done. |
| [kubernetes/](kubernetes/) | Run a Kubernetes Job (or init container) that uses enveloper to inject env vars. |
| [cicd/](cicd/) | GitHub Actions (or similar CI) that pulls secrets and uses `export` / `unexport`. |
| [shell/](shell/) | Plain shell script: load secrets with `eval "$(enveloper export ...)"`, run app, then unexport. |
| [github-secrets/](github-secrets/) | Push keychain (or file) values into **GitHub Actions repository secrets** via `enveloper push --service github`. |
| [sdk/](sdk/) | Load secrets in a **Python script** with the SDK (`load_dotenv`, `dotenv_values`); requires `pip install enveloper[sdk]`. |
| [domains-projects-versioning/](domains-projects-versioning/) | Organize secrets by **domain**, **project**, and **semver version**; list domains/projects, set/get by version. |

## sample.env

The [sample.env](sample.env) file is the same as the one in the project root. It defines variables such as `MY_API_KEY`, `MY_API_SECRET`, and `LEVEL_SET`. Use it to:

- Import into the keychain: `enveloper import sample.env -d mydomain -p myproject`
- Reference in docs and examples as the canonical “what gets loaded” set.

No secrets are committed; the file is a template. Replace values with real secrets when you import.
