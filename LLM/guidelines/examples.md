# Examples guidelines for LLMs

How the **examples/** folder is structured and how to add or change examples.

## Purpose of examples

Examples show users how to use enveloper **without committing `.env` files**: import, export (unix), unexport, and optional push/pull to cloud. Each example is self-contained with a README and, where useful, a script or config file.

## Layout

- **`examples/README.md`** — Index of all examples, concepts (import/export/unexport), prerequisites, and link to **sample.env**.
- **`examples/sample.env`** — Template env file (e.g. `MY_API_KEY`, `LEVEL_SET`); users import it into keychain or use it with the file store in tests.
- **`examples/<name>/`** — One directory per example (e.g. `docker/`, `makefile/`, `sdk/`, `domains-projects-versioning/`).
- Each example directory should have:
  - **README.md** — What the example does, how to run it, and how it integrates with sample.env (and optionally domain/project/version).
  - Optional script or config (e.g. `run_with_secrets.sh`, `Makefile`, `app.py`, `job.yaml`, `github-actions.yml`).

## Adding a new example

1. Create **`examples/<name>/`** with at least a **README.md**.
2. In the README, document:
   - What the example demonstrates (e.g. “Load secrets in a shell script using export/unexport”).
   - Prerequisites (enveloper installed, optional domain/project or cloud credentials).
   - How to run it (commands or steps).
   - Integration with **sample.env** (import path, domain/project if relevant).
3. Add the example to **`examples/README.md`** in the example index table.
4. Add a short entry and link in **`docs/examples.md`** (and, if desired, in **`docs/index.md`** Examples table).
5. Add **tests** in **`tests/test_examples.py`**:
   - Unit: example dir exists, README (and key files) exist, README contains expected terms (e.g. “export”, “unexport”, “enveloper”).
   - Integration (optional): if the example is runnable with the file store or in-process CLI, add a test that runs it (e.g. subprocess with `ENVELOPER_SERVICE=file` and a temp `.env`, or `cli_runner` + `mock_keyring`).

## Concepts to reflect in examples

- **import** — Load variables from a file into keychain or store.
- **export --format unix** — Emit `export VAR=value` lines; use with `eval` to load into the shell.
- **unexport --format unix** — Emit `unset VAR` lines; use with `eval` to clear.
- **Domain / project / version** — Optional; document defaults (`_default_`, `1.0.0`) and that they can differ across keychains and cloud providers when relevant.

## Existing examples (reference)

- **docker/** — Dockerfile, entrypoint, app.sh; host inject or container pulls from AWS.
- **makefile/** — Makefile with demo target using export/unexport.
- **kubernetes/** — Job YAML that runs enveloper in the cluster.
- **cicd/** — GitHub Actions workflow (pull, export, unexport).
- **shell/** — `run_with_secrets.sh` (export, run, unexport).
- **github-secrets/** — Push keychain to GitHub Secrets via `enveloper push --service github`.
- **sdk/** — Python script using `load_dotenv` and `dotenv_values`.
- **domains-projects-versioning/** — Domain, project, semver version; README and demo.sh.
