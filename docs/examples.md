# Examples

This page describes runnable examples that show how to use enveloper so that **secrets stay out of `.env` files** and are loaded from the system keychain or a cloud secret store (e.g. AWS SSM) at runtime. The examples live in the [examples/](https://github.com/raminf/enveloper/tree/main/examples) folder in the repository.

## Concepts

- **`import`** — Load variables from a file (e.g. `sample.env`) into the keychain or cloud store. Use this once to populate the store; no need to keep a `.env` in the repo.
- **`export --format unix`** — Emit shell commands that set environment variables. Use with `eval` to load those values into the current process.
- **`unexport --format unix`** — Emit shell commands that unset those variables. Use with `eval` to clear them from the environment when done.

All examples use the same **domain** and **project** as the sample.env comments: `--domain mydomain --project myproject` (or `-d mydomain -p myproject`). You can change these to match your own naming.

## Prerequisites

1. **CLI-only** (scripts, Make, Docker, CI): `pip install enveloper` or `pip install enveloper[aws]` (or another cloud backend).
2. **Python apps** that load secrets at runtime: `pip install enveloper[sdk]` or `pip install enveloper[all]`.
3. (Optional) Import the example env into your keychain: `enveloper import sample.env --domain mydomain --project myproject`.

---

## Docker { #docker }

Run a container that loads secrets from keychain or AWS (no `.env` file in the image).

- **Host injects env**: On the host, run `eval "$(enveloper export --format unix)"`, then `docker run -e MY_API_KEY -e MY_API_SECRET -e LEVEL_SET ...`.
- **Container pulls from AWS**: Image includes enveloper; entrypoint runs `enveloper pull` then `eval "$(enveloper export --format unix)"` then your app.

**Files**: [examples/docker/](https://github.com/raminf/enveloper/tree/main/examples/docker) — Dockerfile, entrypoint.sh, app.sh, README.

---

## Makefile { #makefile }

Use enveloper in a Makefile: load env for targets via `eval "$$(enveloper export --format unix)"`, then optionally run `make unexport` to clear variables.

**Files**: [examples/makefile/](https://github.com/raminf/enveloper/tree/main/examples/makefile) — Makefile, README.

---

## Kubernetes { #kubernetes }

Run a Kubernetes Job (or init container) that uses enveloper to pull from AWS SSM and inject env vars at runtime. No `.env` file in the image.

**Files**: [examples/kubernetes/](https://github.com/raminf/enveloper/tree/main/examples/kubernetes) — job.yaml, README.

---

## CI/CD { #cicd }

GitHub Actions (or similar CI) that install enveloper, pull secrets from AWS (or import from a secret), run `eval "$(enveloper export --format unix)"`, run build steps, then `eval "$(enveloper unexport ...)"` to clear.

**Files**: [examples/cicd/](https://github.com/raminf/enveloper/tree/main/examples/cicd) — github-actions.yml, README.

---

## Shell script { #shell }

Plain shell script: load secrets with `eval "$(enveloper export ...)"`, run your app, then `eval "$(enveloper unexport ...)"` to clear.

**Files**: [examples/shell/](https://github.com/raminf/enveloper/tree/main/examples/shell) — run_with_secrets.sh, README.

---

## GitHub Secrets { #github-secrets }

Push keychain (or file) values into **GitHub Actions repository secrets** via `enveloper push --service github --repo OWNER/REPO`. Requires the `gh` CLI and `gh auth login`. No `.env` file is committed; values are sent via `gh secret set`.

**Files**: [examples/github-secrets/](https://github.com/raminf/enveloper/tree/main/examples/github-secrets) — push-to-github.sh, README.

See also [GitHub Secrets](github-secrets.md) for more detail.

---

## Python SDK { #sdk }

Load secrets in a **Python script** with the SDK: `load_dotenv()` to populate `os.environ`, or `dotenv_values()` to get a dict. Requires `pip install enveloper[sdk]`.

**Files**: [examples/sdk/](https://github.com/raminf/enveloper/tree/main/examples/sdk) — app.py, README.

See also [SDK](sdk.md) for the full API.

---

## Domains, projects & versioning { #domains-projects-versioning }

Organize secrets by **domain** (e.g. `dev`, `staging`, `prod`), **project** (e.g. `myapp`, `worker`), and **semver version** (e.g. `1.0.0`, `2.0.0`). Keys are stored under `{prefix}/{domain}/{project}/{version}/{name}`. When omitted, domain and project default to `_default_` (or `ENVELOPER_DOMAIN` / `ENVELOPER_PROJECT`); version defaults to `1.0.0`. Defaults and key layout can differ across keychains and cloud providers; see [Domains, projects & versioning](domains-projects-versioning.md). Use `list domain`, `list project`, and `--version` for get/set/import/export.

**Files**: [examples/domains-projects-versioning/](https://github.com/raminf/enveloper/tree/main/examples/domains-projects-versioning) — README, demo.sh.

See also [Domains, projects & versioning](domains-projects-versioning.md) and [Versioning](versioning.md).

---

## sample.env

The [examples/sample.env](https://github.com/raminf/enveloper/tree/main/examples/sample.env) file defines variables such as `MY_API_KEY`, `MY_API_SECRET`, and `LEVEL_SET`. Use it to import into the keychain: `enveloper import sample.env -d mydomain -p myproject`. No secrets are committed; the file is a template.
