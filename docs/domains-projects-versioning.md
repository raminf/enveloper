# Domains, projects, and versioning

Secrets in enveloper are organized by **domain**, **project**, and **version**. The key hierarchy is:

```
{prefix}/{domain}/{project}/{version}/{name}
```

For example: `envr/prod/myapp/1.0.0/API_KEY`.

## Domain

A **domain** is a scope such as an environment or subsystem:

- **Environments**: `dev`, `staging`, `prod`
- **Subsystems**: `payments`, `api`, `worker`

Use `-d` / `--domain` in the CLI, or `ENVELOPER_DOMAIN` and the `domain` parameter in the SDK.

## Project

A **project** is a namespace under a domain (e.g. an app or service name):

- `myapp`, `worker`, `api`

Use `-p` / `--project` in the CLI, or `ENVELOPER_PROJECT` and the `project` parameter in the SDK.

## Defaults

When you omit domain or project, enveloper uses **defaults** so that a single scope is still well-defined:

| Scope   | Default        | How it's resolved |
|--------|----------------|--------------------|
| Domain | `_default_`   | `ENVELOPER_DOMAIN` env var, or config, or `_default_`. |
| Project| `_default_`   | `ENVELOPER_PROJECT` env var, or config (e.g. `.enveloper.toml`), or `_default_`. |
| Version| `1.0.0`       | `ENVELOPER_VERSION` env var, or `1.0.0`. |

So `enveloper get API_KEY` (with no `-d` or `-p`) reads from domain `_default_` and project `_default_` at version `1.0.0`. You can set `ENVELOPER_DOMAIN` and `ENVELOPER_PROJECT` (and optionally `ENVELOPER_VERSION`) so that all commands in that shell use the same scope without passing flags every time.

## Keychains and cloud providers

Defaults and how domain/project/version are represented **can differ across backends**:

- **Local keychain** — Uses the hierarchy above; domain and project default to `_default_` when not set. Keys are stored under a single keyring service with composite names.
- **File store** — A single `.env` file has no real domain/project structure; `list domain` returns `_default_` if any keys exist. Domain and project are effectively ignored for key layout; the file is flat.
- **AWS SSM** — Uses path-based parameters; each store defines a prefix (and optionally uses domain/project in the path). Default namespace and path layout are specific to the AWS store.
- **GitHub Secrets** — Secret names are flat (e.g. `API_KEY`); the store may use a naming convention that encodes domain/project. Defaults and naming can differ from the keychain.
- **GCP, Azure, Vault, Alibaba** — Each provider has its own prefix/segment rules and default namespace. Check the store’s `build_default_prefix` and docs for that backend.

When you **push** or **pull** between backends (e.g. keychain → AWS), the same logical domain/project/version are mapped into that backend’s key or path format. The semantics (which secrets belong to which domain/project) are preserved even though the underlying key names or paths may look different.

## Version (semver)

**Version** uses [semantic versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`), e.g. `1.0.0`, `2.0.0`. Use it for:

- **Rollback**: Keep previous config versions; switch by changing `--version`.
- **Environment separation**: Same project name with different versions per release.
- **A/B or canary**: Load version `2.0.0` for a subset of traffic.

Use `-v` / `--version` in the CLI, or `ENVELOPER_VERSION` and the `version` parameter in the SDK. Default is `1.0.0`.

## CLI

```bash
# List all domains that have secrets
enveloper list domain

# List all projects under a domain
enveloper list project --domain prod

# Set/get with domain, project, and version
enveloper set API_KEY secret -d prod -p myapp -v 1.0.0
enveloper get API_KEY -d prod -p myapp -v 1.0.0

# Import/export with version
enveloper import .env -d staging -p myapp -v 2.0.0
eval "$(enveloper export -d prod -p myapp -v 2.0.0 --format unix)"
```

## SDK

```python
from enveloper import load_dotenv, dotenv_values

# Load by domain and project (default version 1.0.0)
load_dotenv(domain="prod", project="myapp")

# Load a specific version
load_dotenv(domain="prod", project="myapp", version="2.0.0")

# Get dict for a version (e.g. compare or pass to code)
v1 = dotenv_values(domain="prod", project="myapp", version="1.0.0")
v2 = dotenv_values(domain="prod", project="myapp", version="2.0.0")
```

## Runnable example

See the [domains-projects-versioning example](https://github.com/raminf/enveloper/tree/main/examples/domains-projects-versioning): README and `demo.sh` show set/list/get with different domain, project, and version.

## See also

- [Versioning](versioning.md) — Full semver behavior, use cases, cloud stores, migration.
- [Technical Details](technical-details.md) — Key composition and store interface.
- [Examples](examples.md#domains-projects-versioning) — All runnable examples.
