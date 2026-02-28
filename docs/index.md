# enveloper

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
enveloper import sample.env --domain dev

# List what's stored

enveloper list
```

<img src="https://github.com/raminf/enveloper/raw/main/media/quickstart-keychain.png" width="80%" alt="Import and list values" />

```bash
# Load local environment settings from keychain

eval "$(enveloper --domain dev export --format unix)"

# Values are loaded into local environment variables. 
# Use in Makefile, shell scripts, etc. 
# 'unix' format works for Linux, Mac, and Windows WSL. 
# For Windows Powershell, use 'win' as format.

# When done, you can use 'unexport' command to remove the set of env variables

eval "$(enveloper --domain dev unexport --format unix)"
```

<img src="https://github.com/raminf/enveloper/raw/main/media/quickstart-export.png" width="80%" alt="Export from keychain to environment then unexport to clear out" />

```bash
# Push to AWS SSM - assume AWS_EXPORT is set or default is configured 

enveloper --service aws --domain dev push
```
<img src="https://github.com/raminf/enveloper/raw/main/media/quickstart-aws.png" width="80%" alt="Push all values in doman from keychain to AWS service" />

```bash
# Verify that they got pushed in AWS console for System Store > Parameters

enveloper --service aws list --domain dev
```
<img src="https://github.com/raminf/enveloper/raw/main/media/quickstart-aws-list.png" width="50%" alt="Env values in AWS SSM" />


```bash
# Pull from AWS SSM into local keychain

enveloper --service aws --domain dev pull

# Clear environment settings
enveloper --domain dev clear
```
<img src="https://github.com/raminf/enveloper/raw/main/media/quickstart-clear.png" width="50%" alt="Clear settings from keychain" />


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

[GNU AGPL v3.0 or later](LICENSE)