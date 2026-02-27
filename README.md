# enveloper

<img src="media/enveloper.svg" width="100%" alt="Envelope Services" />

Manage environment secrets via your system keychain or cloud secret stores. Don't leave exposed `.env` files laying about your filesystem.

## Installation

```bash
pip install enveloper            # CLI only
pip install enveloper[sdk]       # CLI + SDK (load_dotenv / dotenv_values)
pip install enveloper[all]       # CLI + SDK + all cloud backends
```

## Quick Start

```bash
# Import an existing .env file into the keychain
enveloper import sample.env --domain dev

# List what's stored
enveloper list

<img src="media/enveloper-keychain.png" width="80%" alt="Envelope Keychain" />

# Load local environment settings from keychain, then once done, get rid of them

eval "$(enveloper --domain dev export --format unix)"

# Unexport to remove the set of env variables after a build
eval "$(enveloper --domain dev unexport --format unix)"

<img src="media/enveloper-export.png" width="80%" alt="Envelope Keychain" />

# Push to AWS SSM
enveloper --service aws --domain dev push

<img src="media/enveloper-aws.png" width="80%" alt="Envelope Keychain" />

# Verify that they worked

<img src="media/enveloper-aws-list.png" width="80%" alt="Envelope Keychain" />


# Pull from AWS SSM into local keychain

enveloper --service aws --domain dev pull

# Clear environment settings

<img src="media/enveloper-clear.png" width="80%" alt="Envelope Keychain" />


```

## Features

- Backward compatible with `.env` files
- Store values in local keychains (Mac, Linux, Windows), or cloud service secret stores (see below)
- Versioning
- Use in CI/CD, including Github Actions.
- Support for hierarchical settings via _domain_ and _project_ sets.


## Supported Backends

| Backend | Description |
|---------|-------------|
| **Local Keychain** | macOS Keychain, Linux Secret Service, Windows Credential Locker |
| **File** | Plain `.env` files |
| **AWS SSM** | AWS Systems Manager Parameter Store |
| **GitHub** | GitHub Actions secrets |
| **Vault** | HashiCorp Vault KV v2 |
| **GCP** | Google Cloud Secret Manager |
| **Azure** | Azure Key Vault |
| **Alibaba** | Alibaba Cloud KMS Secrets Manager |

## Documentation

- [Step-by-Step Tutorial](docs/step-by-step-tutorial.md) - From sample.env to keychain, builds, and cloud
- [CLI Reference](docs/cli-reference.md) - All commands and options
- [Technical Details](docs/technical-details.md) - Architecture and internals
- [Local Keychain](docs/local-keychain.md) - OS keychain setup and usage
- [Cloud Storage](docs/cloud-storage.md) - Cloud service configuration
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