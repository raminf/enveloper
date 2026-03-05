# Domains, projects, and versioning (semver)

This example shows how to use **domains**, **projects**, and **semantic versioning (semver)** to organize secrets. Keys are stored under a hierarchy: `{prefix}/{domain}/{project}/{version}/{name}` (e.g. `envr/prod/myapp/1.0.0/API_KEY`).

## Concepts

- **Domain** — A scope such as an environment (`dev`, `staging`, `prod`) or subsystem (`payments`, `api`). Use `-d` / `--domain`.
- **Project** — A namespace under a domain, e.g. an app name (`myapp`, `worker`). Use `-p` / `--project`.
- **Version** — Semver (`MAJOR.MINOR.PATCH`, e.g. `1.0.0`, `2.0.0`) for versioned config or rollback. Use `--version` (after the subcommand, e.g. `enveloper set -d prod --version 1.0.0 KEY val`) or `ENVELOPER_VERSION`.

## Defaults

If you don’t set domain or project, enveloper uses **defaults**:

- **Domain** defaults to `_default_` (or the value of `ENVELOPER_DOMAIN` / config).
- **Project** defaults to `_default_` (or the value of `ENVELOPER_PROJECT` / config).
- **Version** defaults to `1.0.0` (or `ENVELOPER_VERSION`).

So `enveloper get API_KEY` with no `-d` or `-p` reads from domain `_default_`, project `_default_`, version `1.0.0`. You can set `ENVELOPER_DOMAIN` and `ENVELOPER_PROJECT` in your environment so all commands in that shell use the same scope.

## Keychains and cloud providers

Defaults and how domain/project/version are stored **can differ across backends**. The local keychain uses the hierarchy above with `_default_` when omitted. The **file store** is flat (a single `.env`) and doesn’t really have domains; **AWS SSM**, **GitHub Secrets**, **GCP**, **Azure**, and others each use their own path or naming conventions. When you push or pull between backends, the same logical domain/project/version are mapped into that backend’s format. See [Domains, projects & versioning](../../docs/domains-projects-versioning.md) in the docs for details.

## CLI examples

### List domains and projects

After storing secrets with different domain/project, list them:

```bash
# List all domains that have secrets
enveloper list domain

# List all projects under a domain
enveloper list project --domain prod
```

### Set and get with domain and project

```bash
# Store per environment (domain) and app (project)
enveloper set API_KEY key-for-dev  -d dev   -p myapp
enveloper set API_KEY key-for-prod -d prod  -p myapp

# Get from a specific domain/project
enveloper get API_KEY -d prod -p myapp
```

### Set and get with version (semver)

```bash
# Store different config versions (e.g. for rollback or A/B)
# Use --version after the subcommand (top-level -v is verbose)
enveloper set -d prod -p myapp --version 1.0.0 DB_URL postgres://v1
enveloper set -d prod -p myapp --version 2.0.0 DB_URL postgres://v2

# Get a specific version
enveloper get -d prod -p myapp --version 1.0.0 DB_URL
enveloper get -d prod -p myapp --version 2.0.0 DB_URL
```

### Import and export with domain, project, and version

```bash
# Import into a specific scope
enveloper import sample.env -d staging -p myapp --version 1.0.0

# Export a specific version to env
eval "$(enveloper export -d prod -p myapp --version 2.0.0 --format unix)"

# Default version is 1.0.0 if not set (or use ENVELOPER_VERSION)
enveloper list keys -d prod -p myapp --version 1.0.0
```

## SDK examples

```python
from enveloper import load_dotenv, dotenv_values

# Load by domain and project
load_dotenv(domain="prod", project="myapp")

# Load a specific semver version
load_dotenv(domain="prod", project="myapp", version="2.0.0")

# Get a dict for a specific version (e.g. for rollback comparison)
v1 = dotenv_values(domain="prod", project="myapp", version="1.0.0")
v2 = dotenv_values(domain="prod", project="myapp", version="2.0.0")
```

## Run the demo script

From the repository root, run the demo to populate a few domain/project/version combinations and list them:

```bash
./examples/domains-projects-versioning/demo.sh
```

The script sets keys under `dev`/`prod`, `myapp`/`worker`, and versions `1.0.0`/`2.0.0`, then runs `list domain`, `list project`, and `get` for different scopes. It uses the local keychain (no cloud required).

## Files in this folder

| File | Purpose |
|------|--------|
| [README.md](README.md) | This file: domains, projects, semver usage. |
| [demo.sh](demo.sh) | Demo script: set/list/get with different domain, project, and version. |

## See also

- [Versioning](../../docs/versioning.md) — Full semver docs, use cases, cloud store behavior.
- [Technical Details](../../docs/technical-details.md) — Key composition and store interface.
