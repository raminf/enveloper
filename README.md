# enveloper

<img src="media/envelope.svg" width="32" height="32" alt="Envelope icon" />

Manage `.env` secrets via your system keychain, plain `.env` files, or optional cloud secret stores.

Stop storing your secrets in local `.env` files. Reduce exposure to LLMs and Agents!

You can use **`file`** as a backward-compatible service to work with regular `.env` files (read, write, list, import, export), use the OS keychain (default) sync your environment variables with cloud services:

- **Local keychain** (default): 
  - MacOS Keychain
  - Linux Secret Service
  - Windows Credential Locker
- **File** (`file`): plain `.env` files — use `--service file` and optional `--path` (default `.env`)
- **Sync with cloud backends:**
  - **AWS SSM** Parameter Store (`aws`)
  - **GitHub** Actions secrets (`github`)
  - **HashiCorp Vault** KV v2 (`vault`)
  - **Google Cloud** Secret Manager (`gcp`)
  - **Azure** Key Vault (`azure`)
  - **Alibaba Cloud** KMS Secrets Manager (`aliyun`)

You can run the CLI as **`enveloper`** or **`envr`** (same binary). It manages individual values, syncs to cloud, and can be use inside scripts and `Makefiles`. It also supports bulk **import/export** in the following formats:

- **dotenv**
- **JSON**
- **YAML**

There's also an optional Python **SDK**, compatible with [python-dotenv](https://pypi.org/project/python-dotenv/) (`load_dotenv` / `dotenv_values`) but instead of relying on local `.env` file, it loads values from your secure keychain or cloud service secret manager.


## Installation

```bash
pip install enveloper              # CLI only
pip install enveloper[sdk]         # CLI + SDK (load_dotenv / dotenv_values)
pip install enveloper[cli,sdk]     # CLI + SDK (same as [sdk])
pip install enveloper[aws]         # CLI + AWS SSM and Lambda support (boto3)
pip install enveloper[vault]       # CLI + HashiCorp Vault KV v2 (hvac)
pip install enveloper[gcp]        # CLI + GCP Secret Manager
pip install enveloper[azure]       # CLI + Azure Key Vault (secrets)
pip install enveloper[alibaba]     # CLI + Alibaba Cloud KMS Secrets Manager
pip install enveloper[all]        # CLI + SDK + AWS + Vault + GCP + Azure + Alibaba
```

## CLI Quick Start

The CLI can be run as **`enveloper`** or **`envr`** (same binary).

```bash
# Import your existing .env file into the keychain
enveloper import .env --domain {domain-name}

# List what's stored
enveloper list

# Export for a build (use with eval in Makefiles/scripts)
eval "$(enveloper export --domain {domain-name})"

# Push to AWS SSM Parameter Store (you provide the prefix)
enveloper push --service aws --domain {domain-name} --prefix /myproject/prod/

# Pull from AWS SSM into local keychain
enveloper pull --service aws --domain {domain-name} --prefix /myproject/prod/

# Push to GitHub Actions Secrets
enveloper push --service github --domain {domain-name}

# Same pattern for other stores: --service vault, gcp, azure, aliyun
# List all service providers: enveloper service
```

## Import and export

### `.env` format

Import:

`enveloper import .env -d {domain-name}`  

Export, for injecting into shell environment:

 `eval "$(enveloper export -d {domain-name})"` 

Export back out to and `.env` file:

`enveloper export -d {domain-name} -o .env`

### JSON/YAML

Values may be imported and exported as `JSON` or `YAML` for use in Docker, CDK, or other project formats.

Input must be an object (flat `{"KEY": "value"}` or nested 
```json
{
  "{domain-name}": 
    {"KEY": "value",
     ...
    }
}
```

They may also be nested with projects:

```json
{
  "{domain-name}": 
    { "{project-name}":
      {
        "KEY": "value",
        ...
      }
    }
}
```

Export format is a flat key-value for the chosen domain.

Import from JSON (or `--format yaml`):

`enveloper import secrets.json --format json -d {domain-name}`
 
Export to JSON (or `--format yaml`):

`enveloper export -d aws --format json -o secrets.json`


## Using the SDK

Install with `pip install enveloper[sdk]` or `pip install enveloper[cli,sdk]`. 

Same idea as [python-dotenv](https://pypi.org/project/python-dotenv/), but from the keychain (or another backend). With `load_dotenv` all values are injected into the current session's environment variables (unless you provide the `override` flag).

**Service parameter:** Both `load_dotenv` and `dotenv_values` accept a **`service`** argument (default: `"local"`). When set, values are loaded from that backend instead of the keychain:

- **`service="local"`** (default) — load from the OS keychain (and in Lambda / with `ENVELOPER_USE_SSM`, from SSM first).
- **`service="file"`** — load from a `.env` file; use **`path`** to specify the file (default: `".env"`).
- **`service="aws"`** (or another cloud store name) — load from that cloud store (same config as the CLI).

```python
from enveloper import load_dotenv, dotenv_values

load_dotenv()                                    # default: keychain (project/domain from env or config)
load_dotenv(project="myapp", domain="mydomain")
load_dotenv(service="file", path=".env.local")   # load from file
load_dotenv(service="aws", domain="prod")   # load from AWS SSM
load_dotenv(override=False)                      # don't overwrite existing os.environ

env = dotenv_values(project="myapp", domain="mydomain")
env = dotenv_values(service="file", path=".env")
  db_url = env.get("DATABASE_URL")
```

## Project, domain, and service defaults

You can avoid passing **`--project`**, **`--domain`**, or **`--service`** every time by setting defaults:

| Setting   | Environment variable   | Config file (`.enveloper.toml`) | Default   |
|----------|------------------------|----------------------------------|-----------|
| Project  | `ENVELOPER_PROJECT`    | `[enveloper]` → `project`        | `"default"` |
| Domain   | `ENVELOPER_DOMAIN`     | (per-domain keys under `[enveloper.domains]`) | `"default"` |
| Service  | `ENVELOPER_SERVICE`    | `[enveloper]` → `service`        | `"local"`   |

## SSM in Lambda

With `enveloper[aws]` installed, in AWS Lambda (or `ENVELOPER_USE_SSM=1`), the SDK loads values from **SSM Parameter Store** that follow a common naming convention.

The SDK first checks SSM, then the keychain, then env vars inside the lambda. 

Set `ENVELOPER_SSM_PREFIX` (e.g. `/myapp/prod/`) in Lambda config.

You can also provide an optional `.enveloper.toml` file in your lambda root, or define `ENVELOPER_PROJECT` / `ENVELOPER_DOMAIN` lambda environment variables.

## Platform Setup

Run `enveloper init` after install to configure access to keychains. You only need to do this once after first installing `enveloper`. This helps smooth out your development experience.

### MacOS

`enveloper init` disables login keychain auto-lock. First access may show an “allow keychain” dialog. Click **Always Allow** to avoid having to enter passwords every time.

Optionally, you can configure Touch ID for `sudo`. The `enveloper init` command shows how, by adding `auth sufficient pam_tid.so` to `/etc/pam.d/sudo_local`. 

### Linux

Use gnome-keyring or `kwallet` (auto-unlock at login). `enveloper init` checks to make sure the daemon is running. 

### Windows:

This uses the _Windows Credential Locker_. It is is unlocked with your session. _Windows Hello_ works if it is configured.

## Concepts

### Project + domain

Secrets live under `enveloper:myproject` with keys like `myproj/TWILIO_API_SID`. 

Use **`--project`** / **`-p`**, **`--domain`** / **`-d`**, and **`--service`** / **`-s`** in the CLI, or set **`ENVELOPER_PROJECT`**, **`ENVELOPER_DOMAIN`**, and **`ENVELOPER_SERVICE`** (or the same in `.enveloper.toml`) so you don’t have to pass them every time. 

Note that CLI flags override env vars. 

You can also provide per-project settings in a `.enveloper.toml` file, placed in the project root.

### Service (backend)

Commands that read or write secrets use a **service** backend. You can pass **`--service`** / **`-s`**, or set **`ENVELOPER_SERVICE`** or **`service`** in `.enveloper.toml` so it doesn't need to be provided on the CLI each time. Default is **`local`** if unset.

- **`local`** (default) — OS keychain. Uses project/domain as above.
- **`file`** — Plain `.env` file. Use **`--path`** to specify the file (default: `.env`).
- Any **cloud store name** (e.g. `aws`, `vault`, `gcp`) — values are read from or written to that store (same config as push/pull).

Examples:

- List keys from a `.env` file: `enveloper list --service file --path .env`
- Get a value from AWS SSM: `enveloper get MY_KEY --service aws`
- Import into a file: `enveloper import .env --service file --path .env.local`
- Export from a file: `enveloper export --service file -o backup.env`

To see all available service providers in order (local, file, then cloud stores): **`enveloper service`**. The Documentation column shows clickable links. On macOS in iTerm2, install the [iTerm2 Browser Plugin](https://iterm2.com/browser-plugin.html), then hold **Cmd** and click a link to open it.

### Listing

- The `enveloper list` command uses the current project/domain. 

- `enveloper list -d {domain-name}` lists one domain

- `enveloper list -p {project}` shows one project
- `enveloper list -p {project} -d {domain}` lists both. 
 
Output is a table with masked values.

### Clearing

You can bulk clear values via `enveloper clear` command. **Clear honors the `--service` flag**: it removes _all_ secrets from the current backend (local keychain, file, or cloud store).

- **`enveloper clear`** or **`enveloper clear -s local`** — clears the local keychain for the current project/domain (default domain when `-d` is not set).
- **`enveloper clear -s file [--path .env]`** — clears the `.env` file at the given path (default: `.env`).
- **`enveloper clear -s aws`** (or another cloud store name) — clears all keys under the resolved prefix in that cloud store.

Note that this is **NOT REVERSIBLE.** 

By default, the CLI will ask you to confirm. It is _highly_ recommended you back up with `enveloper export -o backup.env` first (or `enveloper export -s file -o backup.env` when using the file service).

Examples:

- Clear a single domain (keychain): `enveloper clear -d {domain} -p {project}`
- Clear the default domain (keychain): `enveloper clear`
- Clear a .env file: `enveloper clear --service file --path .env.local`
- Clear a cloud store: `enveloper clear --service aws -d {domain}`

#### CI/CD or scripting clearance

If you need to reset all secrets without a prompt, append the **`--quiet`** (`-q`) flag. 

If you do this in an interactive terminal, you will remove __all__ secrets from the selected service. __Use at your own risk!__

## Project Config file

You can define a file in your project root at `.enveloper.toml` to specify defaults. Here is an example:

```toml
[enveloper]
project = "myproject"
service = "local"   # optional: local | file | aws | github | vault | gcp | azure | aliyun
[enveloper.domains.aws]
env_file = "{path-to-project}/.env"
ssm_prefix = "/myproject/dev/"
[enveloper.aws]
profile = "default"
region = "us-west-2"

# Optional: for vault store (push/pull to HashiCorp Vault KV v2)
[enveloper.vault]
url = "http://127.0.0.1:8200"   # or set VAULT_ADDR; omit to use env only
mount = "secret"                 # KV v2 mount point (default "secret")

# Optional: for gcp store (push/pull to Google Cloud Secret Manager)
[enveloper.gcp]
project = "my-gcp-project"        # or set GOOGLE_CLOUD_PROJECT

# Optional: for azure store (push/pull to Azure Key Vault)
[enveloper.azure]
vault_url = "https://my-vault.vault.azure.net/"   # or set AZURE_VAULT_URL

# Optional: for aliyun store (push/pull to Alibaba Cloud KMS Secrets Manager)
[enveloper.aliyun]
region_id = "cn-hangzhou"   # or set ALIBABA_CLOUD_REGION_ID
# access_key_id and access_key_secret optional; default from ALIBABA_CLOUD_ACCESS_KEY_ID / ALIBABA_CLOUD_ACCESS_KEY_SECRET
```

### Storage plugins

AWS SSM, GitHub, HashiCorp Vault, GCP Secret Manager, and Azure Key Vault are implemented as plugins. Additional backends can be added via the `enveloper.stores` entry-point. Each store must implement the full `SecretStore` interface (including `clear()` so that `enveloper clear --service <name>` removes all keys from that backend).

Built-in stores:

- `keychain` (read/write) — local OS keychain
- `aws` (push/pull) — AWS Systems Manager Parameter Store; install `enveloper[aws]`
- `github` (push only) — GitHub Actions secrets
- `vault` (push/pull) — HashiCorp Vault KV v2; install `enveloper[vault]`
- `gcp` (push/pull) — Google Cloud Secret Manager; install `enveloper[gcp]`
- `azure` (push/pull) — Azure Key Vault (secrets); install `enveloper[azure]`
- `aliyun` (push/pull) — Alibaba Cloud KMS Secrets Manager; install `enveloper[alibaba]`

**Vault:** `[enveloper.vault]` with optional `url` and `mount`. Auth via `VAULT_TOKEN` / `VAULT_ADDR`. Path from `--prefix` or domain `ssm_prefix`. Example: `enveloper push --service vault -d aws --prefix myapp/prod`

**GCP Secret Manager:** `[enveloper.gcp]` with `project` (or set `GOOGLE_CLOUD_PROJECT`). Uses Application Default Credentials. Prefix from `--prefix` or domain `ssm_prefix`. Example: `enveloper push --service gcp -d aws --prefix myapp-prod`

**Azure Key Vault:** `[enveloper.azure]` with `vault_url` (or set `AZURE_VAULT_URL`). Uses DefaultAzureCredential. Prefix from `--prefix` or domain `ssm_prefix`. Example: `enveloper push --service azure -d aws --prefix myapp-prod`

**Alibaba Cloud KMS Secrets Manager:** `[enveloper.aliyun]` with optional `region_id` (default `cn-hangzhou`), `access_key_id`, `access_key_secret`; or set `ALIBABA_CLOUD_ACCESS_KEY_ID` and `ALIBABA_CLOUD_ACCESS_KEY_SECRET`. [Getting started with secrets](https://www.alibabacloud.com/help/en/kms/key-management-service/getting-started/getting-started-with-secrets-manager). Example: `enveloper push --service aliyun -d aws --prefix myapp-prod`


## Workflows

### GitHub Actions

To push from keychain, use:

`enveloper push --service github -d {domain} --repo owner/repo`

- In the workflow, you can then use `${{ secrets.API_KEY }}` etc. 
- In `env:`; no enveloper is available in the runner. 
- In a self-hosted runner with keychain, run: `enveloper export -d {domain} --format dotenv` and source the output.

### AWS CodeBuild

- Push to SSM (example): `enveloper push --service aws -d {domain} --prefix /myproject/prod/`.
- Generate snippet: `enveloper generate codebuild-env -d {domain} --prefix /myapp/prod/`. Then copy the `env:` / `parameter-store:` block into `buildspec.yml`.

### AWS Lambda

Youo can push to SSM locally (same as CodeBuild). 

To use in in Lambda: 

1. Install `enveloper[aws]`
2. Call `load_dotenv()` / `dotenv_values()`. The SDK loads from SSM first, then env (set `ENVELOPER_SSM_PREFIX`, e.g. `/myapp/prod/`)
3. Inject SSM as env vars in IaC at deploy time
4. Or Read from SSM at runtime with `boto3`

## CLI Reference

Global options (before the command): **`--project`** / **`-p`**, **`--domain`** / **`-d`**, **`--service`** / **`-s`** (default: `ENVELOPER_SERVICE` or config, else `local`), **`--path`** (for `--service file`, default: `.env`).

For **push** / **pull**, use **`--service`** to specify the cloud store (e.g. **`aws`**, **`github`**, **`vault`**, **`gcp`**, **`azure`**, **`aliyun`**). Push/pull use `--service` for the cloud store; use `--from` (push) or `--to` (pull) for the other side (default: local). Run **`enveloper service`** to list all providers.

```
enveloper init                             Configure OS keychain for frictionless access
enveloper import <file> [-d DOMAIN] [-s SERVICE] [--path PATH] [--format env|json|yaml]   Import into current service
enveloper export [-d DOMAIN] [-s SERVICE] [--path PATH] [--format env|dotenv|json|yaml] [-o FILE]   Export from current service
enveloper get <key> [-d DOMAIN] [-s SERVICE] [--path PATH]   Get a single secret
enveloper set <key> <value> [-d DOMAIN] [-s SERVICE] [--path PATH]   Set a single secret
enveloper list [-d DOMAIN] [-s SERVICE] [--path PATH]       List keys (rich table)
enveloper rm <key> [-d DOMAIN] [-s SERVICE] [--path PATH]   Remove a single secret
enveloper clear [-d DOMAIN] [-s SERVICE] [--path PATH] [--quiet]   Clear all secrets (prompts unless -q)

enveloper push --service <store> [--from local|file] [-d DOMAIN] [--path PATH] [--prefix ...]   Push to cloud store
enveloper pull --service <store> [--to local|file] [-d DOMAIN] [--path PATH] [--prefix ...]   Pull from cloud store

enveloper service                         List service providers (local, file, then cloud stores)
enveloper stores                           List available store plugins
enveloper generate codebuild-env           Generate CodeBuild buildspec YAML
```

## Makefile Integration

```makefile
# Three-tier fallback: CI env vars > enveloper > .env file
ifneq ($(CI),)
  # CI: env vars pre-set
else ifneq ($(shell command -v enveloper 2>/dev/null),)
  $(shell enveloper export -d aws --format dotenv > /tmp/.enveloper-$(USER).env 2>/dev/null)
  -include /tmp/.enveloper-$(USER).env
else ifneq (,$(wildcard .env))
  -include .env
endif
export
```

---

## Development

`Makefile` uses `uv` to build and test.

```
git clone https://github.com/raminf/enveloper.git
cd enveloper
uv sync --extra dev --all-extras
```

## Test

Relies on `pytest`. Run `make test` to run them all.

**Cloud integration tests** (AWS, GCP, Azure) are **disabled by default**. They require live credentials and are skipped unless you set the corresponding env vars and run with the marker:

- **AWS:** `ENVELOPER_TEST_AWS=1`, `ENVELOPER_TEST_AWS_PREFIX=/your-test-prefix/` (optional), then `pytest -m integration_aws tests/integration/`
- **GCP:** `ENVELOPER_TEST_GCP=1`, `ENVELOPER_TEST_GCP_PROJECT=your-project`, Application Default Credentials, then `pytest -m integration_gcp tests/integration/`
- **Azure:** `ENVELOPER_TEST_AZURE=1`, `ENVELOPER_TEST_AZURE_VAULT_URL=https://your-vault.vault.azure.net/`, DefaultAzureCredential, then `pytest -m integration_azure tests/integration/`
- **Alibaba Cloud:** `ENVELOPER_TEST_ALIBABA=1`, `ENVELOPER_TEST_ALIBABA_REGION=cn-hangzhou` (optional), `ALIBABA_CLOUD_ACCESS_KEY_ID`, `ALIBABA_CLOUD_ACCESS_KEY_SECRET`, then `pytest -m integration_alibaba tests/integration/`

## Publishing to PyPI

Uses `twine` and `~/.pypirc`. It uses PyPi tokens (2FA required):

- [PyPI](https://pypi.org/manage/account/token/)
- [TestPyPI](https://test.pypi.org/manage/account/token/)

- To test deployment, run `make publish-test`. This bumps patch version, then uploads to TestPyPI. 
- To publish to PyPi, run `make publish` (PyPI)

Example `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-...
[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-...
```

**GitHub Actions (optional):** The repo includes a workflow that publishes **only** on version tags or when you run it manually (not on every push). Push a tag like `v0.1.9` (matching `version` in `pyproject.toml`) to publish to PyPI, or use **Actions → Publish to PyPI → Run workflow** and choose PyPI or TestPyPI. Configure [trusted publishing](https://docs.pypi.org/trusted-publishers/) on PyPI and TestPyPI and create GitHub Environments `pypi` and `testpypi`; see the comments in [`.github/workflows/publish.yml`](.github/workflows/publish.yml).

Please make sure you change the name of the project otherwise it will conflict with `enveloper`.

---

## Similar Projects

Other tools and libraries for env and secrets management:

| Project | Links | Description | Contrast with Enveloper |
|--------|-------|-------------|-------------------------|
| **python-dotenv** | [PyPI](https://pypi.org/project/python-dotenv/) · [GitHub](https://github.com/theskumar/python-dotenv) | Reads key-value pairs from a `.env` file and sets them as environment variables; compatible `load_dotenv` / `dotenv_values` API. | File-based; Enveloper uses the OS keychain and optional cloud stores (AWS SSM, GitHub), with a dotenv-compatible SDK on top. |
| **python-decouple** | [PyPI](https://pypi.org/project/python-decouple/) · [GitHub](https://github.com/HBNetwork/python-decouple) | Keeps config out of code; reads from `.ini` or `.env` with type casting and defaults. | File-based config; Enveloper stores secrets in the keychain and syncs to cloud, with import/export from dotenv/JSON/YAML. |
| **environs** | [PyPI](https://pypi.org/project/environs/) · [GitHub](https://github.com/sloria/environs) | Parses and validates environment variables (including from `.env`) with type casting and validation. | Focus on env parsing and validation; Enveloper focuses on where secrets live (keychain + cloud) and a CLI for sync. |
| **dynaconf** | [PyPI](https://pypi.org/project/dynaconf/) · [GitHub](https://github.com/dynaconf/dynaconf) | Multi-source config (env, TOML/YAML/JSON, Vault, Redis) with profiles and validation. | Broad config management; Enveloper is keychain-first with a .env-style workflow and push/pull to AWS SSM and GitHub. |
| **keyring** | [PyPI](https://pypi.org/project/keyring/) · [GitHub](https://github.com/jaraco/keyring) | Cross-platform Python API for the system keychain (macOS Keychain, Linux Secret Service, Windows Credential Locker). | Low-level credential storage; Enveloper uses Keyring under the hood and adds project/domain, CLI, dotenv SDK, and cloud sync. |
| **python-dotenv-vault** | [PyPI](https://pypi.org/project/python-dotenv-vault/) · [GitHub](https://github.com/dotenv-org/python-dotenv-vault) | Loads encrypted `.env.vault` files (decrypt at runtime with a key); safe to commit the vault. | Encrypted files in repo; Enveloper keeps secrets in the OS keychain and optionally pushes to SSM/GitHub, no committed secrets. |
| **Doppler** (doppler-sdk) | [PyPI](https://pypi.org/project/doppler-sdk/) · [GitHub](https://github.com/DopplerHQ/python-sdk) | Hosted secrets manager; SDK and CLI inject config into env or fetch at runtime. | SaaS-centric; Enveloper is local-first (keychain) with optional push/pull to AWS and GitHub, no required service. |
| **1Password** (onepassword-sdk) | [PyPI](https://pypi.org/project/onepassword-sdk/) · [GitHub](https://github.com/1Password/onepassword-sdk-python)  . [1Password Environments](https://developer.1password.com/docs/environments/) | Official SDK to read secrets from 1Password vaults (e.g. with service accounts). | 1Password as source of truth; Enveloper uses the OS keychain and optional cloud stores, with a dotenv-style API. |
| **pydantic-settings** | [PyPI](https://pypi.org/project/pydantic-settings/) · [GitHub](https://github.com/pydantic/pydantic-settings) | Pydantic-based settings from env vars and `.env` with validation and type hints. | Settings from env/files with validation; Enveloper is about storing and syncing secrets (keychain + cloud) and exposing them via a dotenv-like API. |
| **SOPS** | [GitHub](https://github.com/getsops/sops) · [getsops.io](https://getsops.io/) | Encrypted editor for secrets in YAML, JSON, ENV, INI; values encrypted (e.g. AWS KMS, GCP KMS, age, PGP). Safe to commit encrypted files. | CLI/binary (Go); encrypts files in repo. Enveloper uses the OS keychain and optional cloud push/pull, with no committed secret files. |
| **dotenv** (Node.js) | [npm](https://www.npmjs.com/package/dotenv) · [GitHub](https://github.com/motdotla/dotenv) | Loads `.env` into `process.env`; zero-dependency, TypeScript declarations. Node counterpart to python-dotenv. | File-based; Enveloper uses the keychain and optional cloud stores with a dotenv-compatible Python API. |
| **dotenv-vault** (Node.js) | [npm](https://www.npmjs.com/package/dotenv-vault) · [Dotenv](https://dotenv.org/docs/dotenv-vault.html) | Encrypted `.env.vault` for Node; decrypt at runtime with `DOTENV_KEY`. Sync and manage envs via Dotenv services. | Encrypted files + optional cloud sync; Enveloper is keychain-first, local, with optional push/pull to AWS SSM and GitHub. |
| **dotenvx** | [dotenvx.com](https://dotenvx.com) · [GitHub](https://github.com/dotenvx/dotenvx) | Encrypted .env from the creator of dotenv; ECIES/AES-256, public key in repo and private key elsewhere. Drop-in for dotenv, run anywhere, multi-environment. | Encrypted .env files in repo; Enveloper uses the OS keychain and optional push/pull to AWS SSM and GitHub, no committed secret files. |
| **varlock** | [varlock.dev](https://varlock.dev) · [GitHub](https://github.com/dmno-dev/varlock) | Schema-driven .env (`.env.schema` with validation, types, redaction). Drop-in for dotenv; plugins (e.g. 1Password); `varlock run` for any language. | Validation and schema in files; Enveloper is keychain-first with a dotenv-style API and push/pull to a number of cloud-providers and GitHub. |
| **fnox** | [GitHub](https://github.com/jdx/fnox) · [fnox.jdx.dev](https://fnox.jdx.dev) | Encrypted or remote secret manager (Rust). Secrets in git (age, KMS) or in cloud (AWS SM/PS, 1Password, Vault, etc.); `fnox.toml`, `fnox exec`, shell integration. | Multi-provider config and encrypted-in-repo; Enveloper is keychain-first with a dotenv-style Python API and push/pull to cloud-providers and GitHub. |
| **latchkey** | [GitHub](https://github.com/imbue-ai/latchkey) | CLI that injects API credentials into curl requests for known services (Slack, GitHub, etc.). Store via `latchkey auth set` or browser; agents use `latchkey curl`. | Per-service auth for API calls; Enveloper is keychain-backed .env with push/pull to cloud-providers and GitHub and a dotenv-style SDK. |
| **envio** | [GitHub](https://github.com/humblepenguinn/envio) | Secure CLI for env vars (Rust). Encrypted profiles; load into terminal or run programs with them. Import/export. | Encrypted local profiles; Enveloper uses OS keychain and optional cloud sync with dotenv-compatible API. |
| **enveil** | [GitHub](https://github.com/GreatScott/enveil) | Hide .env from AI tools (Rust). `.env` holds `ev://` refs; real values in local encrypted store, injected at runtime. `enveil run -- npm start`. | Local encrypted store, no plaintext on disk; Enveloper uses OS keychain and optional cloud push/pull. |

---

## License

MIT. Please feel free to star and fork. PRs most welcome.
