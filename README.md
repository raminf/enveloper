# enveloper

[![CI](https://github.com/raminf/enveloper/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/raminf/enveloper/actions/workflows/ci.yml)
[![License: AGPL-3.0-or-later](https://img.shields.io/badge/License-AGPL--3.0--or--later-blue.svg)](https://spdx.org/licenses/AGPL-3.0-or-later.html)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/badge/ruff-checked-yellow.svg)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-checked-blue.svg)](https://mypy-lang.org/)
[![PyPI version](https://img.shields.io/pypi/v/enveloper.svg)](https://pypi.org/project/enveloper/)

## Background

<img src="https://github.com/raminf/enveloper/raw/main/media/headlines.png" width="100%" alt="News Headlines" />

[ <a href='https://krebsonsecurity.com/2025/05/xai-dev-leaks-api-key-for-private-spacex-tesla-llms/' target='_blank'>KrebsOnSecurity</a>, <a href='https://blog.gitguardian.com/fresh-from-the-docks-uncovering-100-000-valid-secrets-in-dockerhub/' target='_blank'>DockerHub/GitGuardian</a>, <a href='https://blog.gitguardian.com/toyota-accidently-exposed-a-secret-key-publicly-on-github-for-five-years/' target='_blank'>Toyota/GitGuardian</a>]

<hr />

When developing software, there are often secrets that every developer or team need to deal with. These include:

- API keys
- API secrets
- Web passwords
- User-Ids
- User and Administrative Passwords
- Tokens
- Private endpoints
- File paths
- Universal Identifiers
- Authorization keys
- etc.

In some cases, these are inadvertently hard-coded into code, which is then pushed out to shared repositories. There are services to scan for these, but a recommended practice has been to place these in `.env` files. 

<img src="https://github.com/raminf/enveloper/raw/main/media/best-practice-env.png" width="50%" alt="News Headlines" />

[<a href='https://blog.gitguardian.com/secure-your-secrets-with-env/' target='_blank'>GitGuardian</a>]

<hr />

`.env` files are often excluded in `.gitignore` files so they don't get pushed out. But at build time, they can be loaded into the current environment (terminal, Docker, Lambdas, CI/CD instances). The problem is, if you move to a new machine, or want others to work on the code, they need to get a copy of the `.env` file so they can use these shared secrets.

Over time, these `.env` files themselves end up proliferating all over someone's computer, end up in logs, backups, or lost.

Lately, there's also the matter of AI-based agents with access to the local filesystem. Unless specifically excluded  agents can access and read `.env` files, or send them to remote LLMs. Security company Wiz noticed that <a href="https://www.wiz.io/blog/leaking-ai-secrets-in-public-code" target="_blank">"AI-related secret instances constitute a disproportional majority of the findings (4 out of top 5 secrets found were AI-related)"</a>.

<img src="https://github.com/raminf/enveloper/raw/main/media/headline-ai-secrets.png" width="50%" alt="News Headlines" />
<hr />

## Enter `enveloper`

`enveloper` allows you to avoid `.env` files or hard-coded credentials by storing secrets in your own protected system keychain. These can be injected into a build session at runtime, without any risk of inadvertent release.

Local keychains work well for individuals. But what about sharing secrets? Fortunately, cloud-based services have already solved this problem, by offering _Secret Managers_ or _Vaults_ stored in cryptographically secure locations. 

`enveloper` lets you store all your secrets in your local keychain or cloud-based secret managers, and easily move them back and forth or share them without having to leave any data in the open.

<img src="https://github.com/raminf/enveloper/raw/main/media/enveloper.svg" width="100%" alt="Envelope Services" />

Manage environment secrets via your system keychain or cloud secret stores. Don't leave exposed `.env` files laying about your filesystem.

<hr />

## Installation

```bash
pip install enveloper            # CLI only (scripts, Make, Docker, CI)
pip install enveloper[sdk]       # CLI + SDK — recommended for Python apps (load_dotenv / dotenv_values)
pip install enveloper[all]        # CLI + SDK + all cloud backends
```

For Python applications that load secrets at runtime (keychain or cloud), install the **SDK** extra: `pip install enveloper[sdk]`.

**Examples:** Runnable samples for Docker, Makefile, Kubernetes, CI/CD, shell scripts, GitHub Secrets, the Python SDK, and domains/versioning are in the [**examples**](examples/README.md) folder.

## Quick Start

```bash
# Sample .env file
```
<img src="https://github.com/raminf/enveloper/raw/main/media/quickstart-sample.png" width="40%" alt="Sample .env file" />


```bash
# Import an existing .env file into the keychain
enveloper import sample.env --domain dev --project Enveloper
```

Keys are stored in local keychain.

<img src="https://github.com/raminf/enveloper/raw/main/media/keychain-push.png" width="40%" alt="Sample .env file" />

```bash
# List what's stored

enveloper list key --domain dev --project Enveloper
```

<img src="https://github.com/raminf/enveloper/raw/main/media/quickstart-keychain.png" width="80%" alt="Import and list values" />

```bash
# Load local environment settings from keychain

eval "$(enveloper --domain dev --project Enveloper export --format unix)"

# Values are loaded into local environment variables. 
# Use in Makefile, shell scripts, etc. 
# 'unix' format works for Linux, Mac, and Windows WSL. 
# For Windows Powershell, use 'win' as format.
```

<img src="https://github.com/raminf/enveloper/raw/main/media/quickstart-export.png" width="80%" alt="Export from keychain to environment then unexport to clear out" />


```bash
# When done, you can use 'unexport' command to remove the set of env variables

eval "$(enveloper --domain dev --project Enveloper unexport --format unix)"

# Push to cloud service

enveloper --domain dev --project Enveloper push --service aws
```

<img src="https://github.com/raminf/enveloper/raw/main/media/aws-terminal-push.png" width="80%" alt="Push all values from keychain to cloud" />

In the console, we can verify that the values are stored (in the case of AWS, in the SSM Parameter Store)

<img src="https://github.com/raminf/enveloper/raw/main/media/aws-console-push.png" width="80%" alt="AWS Service Console" />

```bash
# Verify that they got pushed in AWS console for System Store > Parameters

enveloper list key --domain dev --project Enveloper --service aws
```
<img src="https://github.com/raminf/enveloper/raw/main/media/aws-terminal-list-key.png" width="80%" alt="Env values in AWS SSM" />


```bash
# Pull from AWS SSM into local keychain

enveloper pull --domain dev --project Enveloper --service aws

# Clear environment settings
enveloper clear --domain dev --project Enveloper --service aws
```
<img src="https://github.com/raminf/enveloper/raw/main/media/aws-terminal-clear.png" width="80%" alt="Clear settings from cloud" />


## Multiple cloud services

<img src="https://github.com/raminf/enveloper/raw/main/media/aws-logo.svg" width="10%" alt="AWS logo" /> 

### Amazon Web Services (aws)

<img src="https://github.com/raminf/enveloper/raw/main/media/aws-terminal-push.png" width="80%" alt="AWS Terminal Push" />

<img src="https://github.com/raminf/enveloper/raw/main/media/aws-console-push.png" width="80%" alt="AWS Console Push " />

<img src="https://github.com/raminf/enveloper/raw/main/media/gcp-logo.svg" width="10%" alt="AWS logo" /> 

### Google Cloud (gcp)

<img src="https://github.com/raminf/enveloper/raw/main/media/gcp-terminal-push.png" width="80%" alt="GCP Terminal Push" />

<img src="https://github.com/raminf/enveloper/raw/main/media/gcp-console-push.png" width="80%" alt="GCP Console Push " />

<img src="https://github.com/raminf/enveloper/raw/main/media/azure-logo.svg" width="10%" alt="AWS logo" /> 

### Microsoft Azure Cloud (azure)

<img src="https://github.com/raminf/enveloper/raw/main/media/azure-terminal-push.png" width="80%" alt="Azure Terminal Push" />

<img src="https://github.com/raminf/enveloper/raw/main/media/azure-console-push.png" width="80%" alt="Azure Console Push " />

<img src="https://github.com/raminf/enveloper/raw/main/media/vault-logo.svg" width="20%" alt="AWS logo" /> 

### Hashicorp Vault (vault)

<img src="https://github.com/raminf/enveloper/raw/main/media/vault-terminal-push.png" width="80%" alt="Vault Terminal Push" />

<img src="https://github.com/raminf/enveloper/raw/main/media/vault-console-push.png" width="50%" alt="Vault Console Push " />

## Features

- Backward compatible with `.env` files.
- Store values in local keychains (Mac, Linux, Windows), or cloud service secret stores (see below).
- Work with individual environment variables or sets.
- Versioning of environment values using [Semantic Versioning](https://semver.org).
- Use in build chains (Make, Gradle, etc.) or CI/CD, including Github Actions.
- Support for hierarchical settings via _domain_ and _project_ sets.


## Supported Backends

| Backend | Description |
|---------|-------------|
| **Local Keychain** | MacOS Keychain, Linux Secret Service, Windows Credential Locker |
| **File** | Plain `.env` files |
| **AWS SSM** | AWS Systems Manager Parameter Store |
| **Vault** | HashiCorp Vault KV v2 |
| **GCP** | Google Cloud Secret Manager |
| **Azure** | Azure Key Vault |
| **Alibaba** | Alibaba Cloud KMS Secrets Manager (untested) |
| **GitHub** | GitHub Actions secrets (coming soon) |

## Documentation

- [Step-by-Step Tutorial](docs/step-by-step-tutorial.md) - From sample.env to keychain, builds, and cloud
- [Examples](examples/README.md) - Docker, Makefile, Kubernetes, CI/CD, shell, GitHub Secrets, SDK, domains/versioning
- [CLI Reference](docs/cli-reference.md) - All commands and options
- [Technical Details](docs/technical-details.md) - Architecture and internals
- [Local Keychain](docs/local-keychain.md) - OS keychain setup and usage
- [Cloud Storage](docs/cloud-storage.md) - Cloud service configuration
- [Cloud Setup Guide](docs/cloud-setup-guide.md) - Azure, GCP, and AWS setup (credentials, IAM/RBAC, testing)
- [Versioning](docs/versioning.md) - Semantic versioning for secrets
- [Domains, projects & versioning](docs/domains-projects-versioning.md) - Organize secrets by domain, project, and semver
- [JSON/YAML](docs/json-yaml.md) - Import/export in JSON and YAML formats
- [SDK](docs/sdk.md) - Python SDK for `load_dotenv` / `dotenv_values`
- [Project Config](docs/project-config.md) - `.enveloper.toml` configuration
- [Config/Env Overrides](docs/config-env-overrides.md) - Priority order for settings
- [Service Backend](docs/service-backend.md) - Backend selection and configuration
- [CI/CD Integration](docs/cicd-integration.md) - GitHub Actions, CodeBuild, GitLab CI
- [GitHub Secrets](docs/github-secrets.md) - Push keychain values into GitHub Actions secrets
- [Makefile Integration](docs/makefile-integration.md) - Build system integration
- [Other Projects](docs/other-projects.md) - Comparison with similar tools
- [Development](docs/development.md) - Contributing and development
- [Adding Stores](docs/adding-stores.md) - Creating custom store plugins
- [Publishing](docs/publishing.md) - Publishing to PyPI
- [Security](docs/security.md) - Secure data storage and access control
- [Disclosures](docs/disclosures.md) - Disclosures and confessions
- [License](docs/license.md) - AGPL-3.0-or-later


## License

[GNU AGPL v3.0 or later](LICENSE)