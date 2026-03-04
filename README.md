# enveloper

[![CI](https://github.com/raminf/enveloper/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/raminf/enveloper/actions/workflows/ci.yml)
[![License: AGPL-3.0-or-later](https://img.shields.io/badge/License-AGPL--3.0--or--later-blue.svg)](https://spdx.org/licenses/AGPL-3.0-or-later.html)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/badge/ruff-checked-yellow.svg)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-checked-blue.svg)](https://mypy-lang.org/)
[![PyPI version](https://img.shields.io/pypi/v/enveloper.svg)](https://pypi.org/project/enveloper/)

<img src="https://github.com/raminf/enveloper/raw/main/media/enveloper.svg" width="100%" alt="Envelope Services" />

Manage environment secrets via your system keychain or cloud secret stores. Don't leave exposed `.env` files laying about your filesystem.

## Installation

```bash
pip install enveloper            # CLI only
pip install enveloper[sdk]       # CLI + SDK (load_dotenv / dotenv_values)
pip install enveloper[all]       # CLI + SDK + all cloud backends
```

## Quick Start

```bash
# Sample .env file
```
<img src="https://github.com/raminf/enveloper/raw/main/media/quickstart-sample.png" width="50%" alt="Sample .env file" />


```bash
# Import an existing .env file into the keychain
enveloper import sample.env --domain dev --project Enveloper

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

### Amazon Web Services (aws)

<img src="https://github.com/raminf/enveloper/raw/main/media/aws-terminal-push.png" width="80%" alt="AWS Terminal Push" />

<img src="https://github.com/raminf/enveloper/raw/main/media/aws-console-push.png" width="80%" alt="AWS Console Push " />

### Google Cloud (gcp)

<img src="https://github.com/raminf/enveloper/raw/main/media/gcp-terminal-push.png" width="80%" alt="GCP Terminal Push" />

<img src="https://github.com/raminf/enveloper/raw/main/media/gcp-console-push.png" width="80%" alt="GCP Console Push " />

### Microsoft Azure Cloud (azure)

<img src="https://github.com/raminf/enveloper/raw/main/media/azure-terminal-push.png" width="80%" alt="Azure Terminal Push" />

<img src="https://github.com/raminf/enveloper/raw/main/media/azure-console-push.png" width="80%" alt="Azure Console Push " />

### Hashicorp Vault (vault)

<img src="https://github.com/raminf/enveloper/raw/main/media/vault-terminal-push.png" width="80%" alt="Vault Terminal Push" />

<img src="https://github.com/raminf/enveloper/raw/main/media/vault-console-push.png" width="80%" alt="Vault Console Push " />

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
- [CLI Reference](docs/cli-reference.md) - All commands and options
- [Technical Details](docs/technical-details.md) - Architecture and internals
- [Local Keychain](docs/local-keychain.md) - OS keychain setup and usage
- [Cloud Storage](docs/cloud-storage.md) - Cloud service configuration
- [Cloud Setup Guide](docs/cloud-setup-guide.md) - Azure, GCP, and AWS setup (credentials, IAM/RBAC, testing)
- [Versioning](docs/versioning.md) - Semantic versioning for secrets
- [JSON/YAML](docs/json-yaml.md) - Import/export in JSON and YAML formats
- [SDK](docs/sdk.md) - Python SDK for `load_dotenv` / `dotenv_values`
- [Project Config](docs/project-config.md) - `.enveloper.toml` configuration
- [Config/Env Overrides](docs/config-env-overrides.md) - Priority order for settings
- [Service Backend](docs/service-backend.md) - Backend selection and configuration
- [CI/CD Integration](docs/cicd-integration.md) - GitHub Actions, CodeBuild, GitLab CI
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