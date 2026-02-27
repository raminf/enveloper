# enveloper

![Envelope Services](media/enveloper.svg){ width="100%" }

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
enveloper import sample.env --domain prod

# List what's stored
enveloper list

# Export for a build
eval "$(enveloper --domain prod export --format unix)"

# Unexport to remove the set of env variables after a build
eval "$(enveloper --domain prod unexport --format unix)"

# Push to AWS SSM
enveloper --service aws --domain prod push

# Pull from AWS SSM
enveloper --service aws --domain prod pull
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

- [Step-by-Step Tutorial](step-by-step-tutorial.md) - From sample.env to keychain, builds, and cloud
- [CLI Reference](cli-reference.md) - All commands and options
- [Technical Details](technical-details.md) - Architecture and internals
- [Local Keychain](local-keychain.md) - OS keychain setup and usage
- [Cloud Storage](cloud-storage.md) - Cloud service configuration
- [Versioning](versioning.md) - Semantic versioning for secrets
- [JSON/YAML](json-yaml.md) - Import/export in JSON and YAML formats
- [SDK](sdk.md) - Python SDK for `load_dotenv` / `dotenv_values`
- [Project Config](project-config.md) - `.enveloper.toml` configuration
- [Config/Env Overrides](config-env-overrides.md) - Priority order for settings
- [Service Backend](service-backend.md) - Backend selection and configuration
- [CI/CD Integration](cicd-integration.md) - GitHub Actions, CodeBuild, GitLab CI
- [Makefile Integration](makefile-integration.md) - Build system integration
- [Other Projects](other-projects.md) - Comparison with similar tools
- [Development](development.md) - Contributing and development
- [Adding Stores](adding-stores.md) - Creating custom store plugins
- [Publishing](publishing.md) - Publishing to PyPI
- [Security](security.md) - Secure data storage and access control
- [Disclosures](disclosures.md) - Disclosures and confessions
- [License](license.md) - AGPL-3.0-or-later


## License

[GNU AGPL v3.0 or later](license.md)
