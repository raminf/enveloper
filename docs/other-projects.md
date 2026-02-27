# Other Projects

This document compares `enveloper` with other tools and libraries for environment and secrets management.

## Comparison Table

| Project | Links | Description | Contrast with Enveloper |
|---------|-------|-------------|-------------------------|
| **python-dotenv** | [PyPI](https://pypi.org/project/python-dotenv/) · [GitHub](https://github.com/theskumar/python-dotenv) | Reads key-value pairs from a `.env` file and sets them as environment variables; compatible `load_dotenv` / `dotenv_values` API. | File-based; Enveloper uses the OS keychain and optional cloud stores (AWS SSM, GitHub), with a dotenv-compatible SDK on top. |
| **python-decouple** | [PyPI](https://pypi.org/project/python-decouple/) · [GitHub](https://github.com/HBNetwork/python-decouple) | Keeps config out of code; reads from `.ini` or `.env` with type casting and defaults. | File-based config; Enveloper stores secrets in the keychain and syncs to cloud, with import/export from dotenv/JSON/YAML. |
| **environs** | [PyPI](https://pypi.org/project/environs/) · [GitHub](https://github.com/sloria/environs) | Parses and validates environment variables (including from `.env`) with type casting and validation. | Focus on env parsing and validation; Enveloper focuses on where secrets live (keychain + cloud) and a CLI for sync. |
| **dynaconf** | [PyPI](https://pypi.org/project/dynaconf/) · [GitHub](https://github.com/dynaconf/dynaconf) | Multi-source config (env, TOML/YAML/JSON, Vault, Redis) with profiles and validation. | Broad config management; Enveloper is keychain-first with a .env-style workflow and push/pull to AWS SSM and GitHub. |
| **keyring** | [PyPI](https://pypi.org/project/keyring/) · [GitHub](https://github.com/jaraco/keyring) | Cross-platform Python API for the system keychain (macOS Keychain, Linux Secret Service, Windows Credential Locker). | Low-level credential storage; Enveloper uses Keyring under the hood and adds project/domain, CLI, dotenv SDK, and cloud sync. |
| **python-dotenv-vault** | [PyPI](https://pypi.org/project/python-dotenv-vault/) · [GitHub](https://github.com/dotenv-org/python-dotenv-vault) | Loads encrypted `.env.vault` files (decrypt at runtime with a key); safe to commit the vault. | Encrypted files in repo; Enveloper keeps secrets in the OS keychain and optionally pushes to SSM/GitHub, no committed secrets. |
| **Doppler** (doppler-sdk) | [PyPI](https://pypi.org/project/doppler-sdk/) · [GitHub](https://github.com/DopplerHQ/python-sdk) | Hosted secrets manager; SDK and CLI inject config into env or fetch at runtime. | SaaS-centric; Enveloper is local-first (keychain) with optional push/pull to AWS and GitHub, no required service. |
| **1Password** (onepassword-sdk) | [PyPI](https://pypi.org/project/onepassword-sdk/) · [GitHub](https://github.com/1Password/onepassword-sdk-python) | Official SDK to read secrets from 1Password vaults (e.g., with service accounts). | 1Password as source of truth; Enveloper uses the OS keychain and optional cloud stores, with a dotenv-style API. |
| **pydantic-settings** | [PyPI](https://pypi.org/project/pydantic-settings/) · [GitHub](https://github.com/pydantic/pydantic-settings) | Pydantic-based settings from env vars and `.env` with validation and type hints. | Settings from env/files with validation; Enveloper is about storing and syncing secrets (keychain + cloud) and exposing them via a dotenv-like API. |
| **SOPS** | [GitHub](https://github.com/getsops/sops) · [getsops.io](https://getsops.io/) | Encrypted editor for secrets in YAML, JSON, ENV, INI; values encrypted (e.g., AWS KMS, GCP KMS, age, PGP). Safe to commit encrypted files. | CLI/binary (Go); encrypts files in repo. Enveloper uses the OS keychain and optional cloud push/pull, with no committed secret files. |
| **dotenv** (Node.js) | [npm](https://www.npmjs.com/package/dotenv) · [GitHub](https://github.com/motdotla/dotenv) | Loads `.env` into `process.env`; zero-dependency, TypeScript declarations. Node counterpart to python-dotenv. | File-based; Enveloper uses the keychain and optional cloud stores with a dotenv-compatible Python API. |
| **dotenv-vault** (Node.js) | [npm](https://www.npmjs.com/package/dotenv-vault) · [Dotenv](https://dotenv.org/docs/dotenv-vault.html) | Encrypted `.env.vault` for Node; decrypt at runtime with `DOTENV_KEY`. Sync and manage envs via Dotenv services. | Encrypted files + optional cloud sync; Enveloper is keychain-first, local, with optional push/pull to AWS SSM and GitHub. |
| **dotenvx** | [dotenvx.com](https://dotenvx.com) · [GitHub](https://github.com/dotenvx/dotenvx) | Encrypted .env from the creator of dotenv; ECIES/AES-256, public key in repo and private key elsewhere. Drop-in for dotenv, run anywhere, multi-environment. | Encrypted .env files in repo; Enveloper uses the OS keychain and optional push/pull to AWS SSM and GitHub, no committed secret files. |
| **varlock** | [varlock.dev](https://varlock.dev) · [GitHub](https://github.com/dmno-dev/varlock) | Schema-driven .env (`.env.schema` with validation, types, redaction). Drop-in for dotenv; plugins (e.g., 1Password); `varlock run` for any language. | Validation and schema in files; Enveloper is keychain-first with a dotenv-style API and push/pull to a number of cloud-providers and GitHub. |
| **fnox** | [GitHub](https://github.com/jdx/fnox) · [fnox.jdx.dev](https://fnox.jdx.dev) | Encrypted or remote secret manager (Rust). Secrets in git (age, KMS) or in cloud (AWS SM/PS, 1Password, Vault, etc.); `fnox.toml`, `fnox exec`, shell integration. | Multi-provider config and encrypted-in-repo; Enveloper is keychain-first with a dotenv-style Python API and push/pull to cloud-providers and GitHub. |
| **latchkey** | [GitHub](https://github.com/imbue-ai/latchkey) | CLI that injects API credentials into curl requests for known services (Slack, GitHub, etc.). Store via `latchkey auth set` or browser; agents use `latchkey curl`. | Per-service auth for API calls; Enveloper is keychain-backed .env with push/pull to cloud-providers and GitHub and a dotenv-style SDK. |
| **envio** | [GitHub](https://github.com/humblepenguinn/envio) | Secure CLI for env vars (Rust). Encrypted profiles; load into terminal or run programs with them. Import/export. | Encrypted local profiles; Enveloper uses OS keychain and optional cloud sync with dotenv-compatible API. |
| **enveil** | [GitHub](https://github.com/GreatScott/enveil) | Hide .env from AI tools (Rust). `.env` holds `ev://` refs; real values in local encrypted store, injected at runtime. `enveil run -- npm start`. | Local encrypted store, no plaintext on disk; Enveloper uses OS keychain and optional cloud push/pull. |

## Key Differences

### Enveloper vs. python-dotenv

| Feature | Enveloper | python-dotenv |
|---------|-----------|---------------|
| Storage | OS keychain + cloud | `.env` files only |
| Security | Encrypted at rest | Plain text |
| Team sharing | Push/pull to cloud | Manual file sharing |
| CLI | Full-featured | None |
| SDK | Compatible API | Compatible API |

### Enveloper vs. Dynaconf

| Feature | Enveloper | Dynaconf |
|---------|-----------|----------|
| Primary focus | Secrets management | Config management |
| Storage | Keychain + cloud | Multiple sources |
| CLI | Built-in | None |
| SDK | dotenv-compatible | Custom API |
| Cloud sync | Built-in | Via plugins |

### Enveloper vs. SOPS

| Feature | Enveloper | SOPS |
|---------|-----------|------|
| Storage | Keychain + cloud | Encrypted files |
| Commit to git | No | Yes (encrypted) |
| CLI | Full-featured | File editor |
| SDK | Python | None |
| Cloud sync | Built-in | Manual |

## Choosing the Right Tool

### Use Enveloper When

- You want to keep secrets out of version control
- You need cross-platform keychain support
- You want to sync secrets across team members
- You need a CLI for managing secrets
- You want dotenv-compatible SDK

### Use python-dotenv When

- You're okay with `.env` files in your repo
- You need simple env var loading
- You don't need cross-platform keychain

### Use Dynaconf When

- You need multi-source config management
- You want validation and type casting
- You need profiles for different environments

### Use SOPS When

- You want to commit encrypted secrets to git
- You need encryption with KMS
- You want a file-based workflow

## Contributing

If you'd like to add your project to this list, please open an issue or submit a PR.