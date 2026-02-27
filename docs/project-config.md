# Project Config File

## Overview

The `.enveloper.toml` file in your project root allows you to define default values for project, domain, and service settings. This eliminates the need to pass these values on the command line every time.

## File Location

Place `.enveloper.toml` in your project root directory:

```
myproject/
├── .enveloper.toml
├── src/
├── tests/
└── README.md
```

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
| `project` | `GOOGLE_CLOUD_PROJECT` | GCP project ID |

#### Azure

```toml
[enveloper.azure]
vault_url = "https://my-vault.vault.azure.net/"
```

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `vault_url` | `AZURE_VAULT_URL` | Key Vault URL |

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

```toml
[enveloper]
project = "myapp"
service = "local"

[enveloper.domains.aws]
env_file = "/path/to/.env"
ssm_prefix = "/myapp/dev/"

[enveloper.aws]
profile = "default"
region = "us-west-2"

[enveloper.vault]
url = "http://127.0.0.1:8200"
mount = "secret"

[enveloper.gcp]
project = "my-gcp-project"

[enveloper.azure]
vault_url = "https://my-vault.vault.azure.net/"

[enveloper.aliyun]
region_id = "cn-hangzhou"
```

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