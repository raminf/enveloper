# Project Config File

## Overview

The `.enveloper.toml` file allows you to define default values for project, domain, service, and cloud backend settings. This eliminates the need to pass these values on the command line every time.

## File Location

Config is loaded in this order:

1. **`~/.enveloper/.enveloper.toml`** — If the directory `~/.enveloper` exists and contains `.enveloper.toml`, that file is used (good for a single global config).
2. **Current directory and parents** — Otherwise, enveloper searches **upward from the current working directory** for `.enveloper.toml` (e.g. in your project root).

```
# Option A: global config
~/.enveloper/
└── .enveloper.toml

# Option B: per-project config
myproject/
├── .enveloper.toml
├── src/
└── README.md
```

When you run `enveloper` from `myproject/` or any subdirectory, the resolved config is used. If no file is found, defaults apply and you can still use environment variables or CLI flags.

### Sample config files

The repo includes sample configs (copy and edit as needed):

- **`sample.enveloper.toml`** — Full example with all service sections (AWS, GCP, Azure, Vault, GitHub, Aliyun).
- **`sample.enveloper.minimal.toml`** — Minimal (local keychain only).

Copy to `~/.enveloper/.enveloper.toml` or to your project root as `.enveloper.toml`.

## Basic Structure

```toml
[enveloper]
project = "myproject"
service = "local"
```

## Configuration Options

### Project Settings

```toml
[enveloper]
project = "myproject"
service = "local"
```

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `project` | `ENVELOPER_PROJECT` | Default project name |
| `service` | `ENVELOPER_SERVICE` | Default service backend |

### Domain-Specific Settings

```toml
[enveloper.domains.aws]
env_file = "/path/to/.env"
ssm_prefix = "/myproject/dev/"
```

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `env_file` | N/A | Path to `.env` file for import/export |
| `ssm_prefix` | N/A | Default prefix for AWS SSM |

### Service-Specific Configuration

#### AWS

```toml
[enveloper.aws]
profile = "default"
region = "us-west-2"
```

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `profile` | `AWS_PROFILE` | AWS profile name |
| `region` | `AWS_DEFAULT_REGION` | AWS region |

#### Vault

```toml
[enveloper.vault]
url = "http://127.0.0.1:8200"
mount = "secret"
```

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `url` | `VAULT_ADDR` | Vault server URL |
| `mount` | N/A | KV v2 mount point |

#### GCP

```toml
[enveloper.gcp]
project = "my-gcp-project"
```

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `project` | `ENVELOPER_GCP_PROJECT` or `GOOGLE_CLOUD_PROJECT` | GCP project ID or **Project name** (resolved to project ID); fallback: `gcloud config get-value project` |

#### Azure

```toml
[enveloper.azure]
vault_url = "https://my-vault.vault.azure.net/"
```

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `vault_url` | `ENVELOPER_AZURE_VAULT_URL` | Key Vault URL (full URL or vault name) |

#### GitHub

GitHub repository is passed via the CLI `--repo owner/name` when using push. Optional prefix in config:

```toml
[enveloper.github]
prefix = ""
```

#### Alibaba Cloud

```toml
[enveloper.aliyun]
region_id = "cn-hangzhou"
access_key_id = "..."
access_key_secret = "..."
```

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `region_id` | `ALIBABA_CLOUD_REGION_ID` | Region ID |
| `access_key_id` | `ALIBABA_CLOUD_ACCESS_KEY_ID` | Access key ID |
| `access_key_secret` | `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | Access key secret |

## Complete Example

All services in one `.enveloper.toml` (use only the sections you need):

```toml
[enveloper]
project = "myapp"
service = "local"

# Optional: per-domain settings (e.g. for AWS SSM prefix)
[enveloper.domains.aws]
env_file = "/path/to/.env"
ssm_prefix = "/myapp/dev/"

# AWS Systems Manager Parameter Store
[enveloper.aws]
profile = "default"
region = "us-west-2"

# HashiCorp Vault KV v2
[enveloper.vault]
url = "http://127.0.0.1:8200"
mount = "secret"

# Google Cloud Secret Manager
[enveloper.gcp]
project = "my-gcp-project"

# Azure Key Vault
[enveloper.azure]
vault_url = "https://my-vault.vault.azure.net/"

# GitHub (repo passed via CLI: --repo owner/repo)
[enveloper.github]
prefix = ""

# Alibaba Cloud KMS Secrets Manager
[enveloper.aliyun]
region_id = "cn-hangzhou"
access_key_id = ""
access_key_secret = ""
```

## Reference: All service options

| Service | Config section | Options | Env fallback |
|---------|----------------|---------|--------------|
| **AWS** | `[enveloper.aws]` | `profile`, `region` | `AWS_PROFILE`, `AWS_DEFAULT_REGION` |
| **GCP** | `[enveloper.gcp]` | `project` | `ENVELOPER_GCP_PROJECT`, `GOOGLE_CLOUD_PROJECT`, `gcloud config` |
| **Azure** | `[enveloper.azure]` | `vault_url` | `ENVELOPER_AZURE_VAULT_URL` |
| **Vault** | `[enveloper.vault]` | `url`, `mount` | `VAULT_ADDR` |
| **GitHub** | `[enveloper.github]` | `prefix` | Repo via CLI `--repo owner/name` only |
| **Aliyun** | `[enveloper.aliyun]` | `region_id`, `access_key_id`, `access_key_secret` | Alibaba env vars |

See [Cloud setup guide](cloud-setup-guide.md) for step-by-step Azure, GCP, and AWS setup (credentials, IAM/RBAC, and testing).

## Priority Order

Configuration values are resolved in this order (highest to lowest priority):

1. **CLI arguments** (e.g., `--project myproject`)
2. **Environment variables** (e.g., `ENVELOPER_PROJECT=myproject`)
3. **Config file** (`.enveloper.toml`)
4. **Default values** (e.g., `"default"`)

## Using with CLI

With the config file in place:

```bash
# These commands use defaults from .enveloper.toml
enveloper list
enveloper export
enveloper import .env

# CLI flags still override config
enveloper list --project otherproject
```

## Using with SDK

```python
from enveloper import load_dotenv, dotenv_values

# Uses project/domain from .enveloper.toml
load_dotenv()
env = dotenv_values()

# Can still override
load_dotenv(project="otherproject")
```

## Environment Variable Reference

| Config Option | Environment Variable | Description |
|---------------|---------------------|-------------|
| `project` | `ENVELOPER_PROJECT` | Project name |
| `domain` | `ENVELOPER_DOMAIN` | Domain name |
| `service` | `ENVELOPER_SERVICE` | Service backend |
| `version` | `ENVELOPER_VERSION` | Version |
| `ssm_prefix` | `ENVELOPER_SSM_PREFIX` | SSM prefix for Lambda |

## Best Practices

1. **Commit to version control** - Include `.enveloper.toml` in git
2. **Use consistent naming** - Follow project conventions
3. **Document defaults** - Add comments explaining choices
4. **Keep paths relative** - Use relative paths when possible
5. **Test configuration** - Verify with `enveloper service`

## Troubleshooting

### Config Not Found

```bash
# Ensure file is in project root
ls -la .enveloper.toml

# Check file permissions
cat .enveloper.toml
```

### Invalid TOML

```bash
# Validate TOML syntax
python -c "import tomllib; tomllib.load(open('.enveloper.toml', 'rb'))"
```

### Service Not Recognized

```bash
# Check available services
enveloper service

# Verify service name in config
cat .enveloper.toml