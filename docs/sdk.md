# SDK

## Overview

The `enveloper` SDK provides a Python API for loading secrets from the local keychain or cloud stores. It's compatible with `python-dotenv`'s `load_dotenv` and `dotenv_values` functions.

You can load from **any service** (local keychain, file, or cloud stores such as AWS SSM, GCP Secret Manager, Azure Key Vault, Vault, Alibaba) and **filter by domain, project, and version**. Only secrets for that scope are returned (e.g. `version="2.0.0"` loads only keys under that version).

## Installation

```bash
# CLI only
pip install enveloper

# CLI + SDK
pip install enveloper[sdk]

# With AWS support
pip install enveloper[aws]

# All extras
pip install enveloper[all]
```

## Basic Usage

### load_dotenv

Injects all secrets into the current session's environment variables.

```python
from enveloper import load_dotenv

# Load from local keychain (default)
load_dotenv()

# Load from specific project/domain
load_dotenv(project="myapp", domain="prod")

# Load from file
load_dotenv(service="file", path=".env.local")

# Load from AWS SSM
load_dotenv(service="aws", domain="prod")

# Load from GCP Secret Manager
load_dotenv(service="gcp", domain="prod")

# Load from Azure Key Vault
load_dotenv(service="azure", domain="prod")

# Load from Alibaba Cloud KMS
load_dotenv(service="aliyun", domain="prod")

# Load from HashiCorp Vault
load_dotenv(service="vault", domain="prod")

# Don't override existing env vars
load_dotenv(override=False)
```

### dotenv_values

Returns a dictionary of secrets without modifying the environment.

```python
from enveloper import dotenv_values

# Get secrets from keychain
env = dotenv_values(project="myapp", domain="prod")

# Get secrets from file
env = dotenv_values(service="file", path=".env")

# Get secrets from AWS SSM
env = dotenv_values(service="aws", domain="prod")

# Get secrets from GCP Secret Manager
env = dotenv_values(service="gcp", domain="prod")

# Get secrets from Azure Key Vault
env = dotenv_values(service="azure", domain="prod")

# Get secrets from Alibaba Cloud KMS
env = dotenv_values(service="aliyun", domain="prod")

# Get secrets from HashiCorp Vault
env = dotenv_values(service="vault", domain="prod")

# Access values
db_url = env.get("DATABASE_URL")
api_key = env.get("API_KEY")
```

## Service Parameter

| Service | Description | Install Extra | Read/Write |
|---------|-------------|---------------|------------|
| `local` (default) | OS keychain | None | Read/Write |
| `file` | Plain `.env` file | None | Read/Write |
| `aws` | AWS SSM Parameter Store | `enveloper[aws]` | Read/Write |
| `github` | GitHub Actions secrets | Built-in | Write-only |
| `vault` | HashiCorp Vault KV v2 | `enveloper[vault]` | Read/Write |
| `gcp` | Google Cloud Secret Manager | `enveloper[gcp]` | Read/Write |
| `azure` | Azure Key Vault | `enveloper[azure]` | Read/Write |
| `aliyun` | Alibaba Cloud KMS | `enveloper[alibaba]` | Read/Write |

### Cloud Service Access

All cloud services support **readonly access** for reading secrets:

```python
from enveloper import dotenv_values

# Read-only access to AWS SSM
env = dotenv_values(service="aws", domain="prod")

# Read-only access to GCP Secret Manager
env = dotenv_values(service="gcp", domain="prod")

# Read-only access to Azure Key Vault
env = dotenv_values(service="azure", domain="prod")

# Read-only access to Alibaba Cloud KMS
env = dotenv_values(service="aliyun", domain="prod")
```

For write operations, use `load_dotenv()` with `override=True` or use the CLI commands:
- `enveloper push` - Push secrets to cloud
- `enveloper pull` - Pull secrets from cloud

## Versioning

The SDK supports reading secrets from specific versions. Pass **version** (semver format) to limit results to that version:

```python
# Load specific version
env = dotenv_values(project="myapp", domain="prod", service="aws", version="1.0.0")

# Default version when omitted is 1.0.0 (or ENVELOPER_VERSION)
env = dotenv_values(project="myapp", domain="prod")
```

When **version** is not specified, the default is `1.0.0` (or `ENVELOPER_VERSION`). Cloud stores and the keychain store keys under a version segment; only keys matching the requested version are returned.

## Key Decoding

The SDK automatically decodes keys from the store format to environment variable names. Composite keys (prefix, domain, project, version, name) are stripped down to the simple name:

```python
# Store key (format depends on store; e.g. prefix/domain/project/version/DATABASE_URL)
# SDK returns: {"DATABASE_URL": "value"}
env = dotenv_values(project="myapp", domain="prod")
```

The store's `key_to_export_name` (and the SDK's use of it) strips prefix, domain, project, and version from keys, leaving only the environment variable name. Prefix and separators are defined per store (see STORES.md).

## Configuration

### Project and Domain

```python
# Using parameters
load_dotenv(project="myapp", domain="prod")

# Using environment variables
import os
os.environ["ENVELOPER_PROJECT"] = "myapp"
os.environ["ENVELOPER_DOMAIN"] = "prod"
load_dotenv()

# Using config file (.enveloper.toml)
# [enveloper]
# project = "myapp"
# domain = "prod"
```

### Version

```python
# Load specific version
load_dotenv(version="1.0.0")

# Get specific version
env = dotenv_values(version="2.0.0")
```

### Path (for file service)

```python
# Load from specific file
load_dotenv(service="file", path=".env.local")

# Get from specific file
env = dotenv_values(service="file", path=".env.production")
```

## AWS Lambda Integration

### Using SSM in Lambda

```python
import os
from enveloper import load_dotenv

# Set SSM prefix in Lambda config
os.environ["ENVELOPER_SSM_PREFIX"] = "/myapp/prod/"

# Load from SSM (first), then keychain, then env vars
load_dotenv()
```

### Using Config File in Lambda

Place `.enveloper.toml` in your Lambda root:

```toml
[enveloper]
project = "myapp"
domain = "prod"
service = "aws"
```

## Advanced Usage

### Conditional Loading

```python
from enveloper import load_dotenv, dotenv_values
import os

# Check if running in Lambda
if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    load_dotenv(service="aws")
else:
    load_dotenv(service="local")
```

### Multiple Sources

```python
from enveloper import load_dotenv, dotenv_values

# Load from keychain first
load_dotenv(service="local")

# Override with file if exists
if os.path.exists(".env.local"):
    load_dotenv(service="file", path=".env.local", override=True)
```

### Error Handling

```python
from enveloper import dotenv_values
import os

try:
    env = dotenv_values(project="myapp", domain="prod")
    db_url = env.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found")
except Exception as e:
    print(f"Error loading secrets: {e}")
```

## Compatibility with python-dotenv

The SDK is designed to be compatible with `python-dotenv`:

| python-dotenv | enveloper |
|---------------|-----------|
| `load_dotenv()` | `load_dotenv()` |
| `dotenv_values()` | `dotenv_values()` |
| `find_dotenv()` | N/A (uses keychain) |
| `get_key()` | N/A (use `dotenv_values`) |

### Migration Guide

**Before (python-dotenv):**
```python
from dotenv import load_dotenv, dotenv_values

load_dotenv()
db_url = os.environ.get("DATABASE_URL")
```

**After (enveloper):**
```python
from enveloper import load_dotenv, dotenv_values

load_dotenv()
db_url = os.environ.get("DATABASE_URL")
```

## Best Practices

1. **Use local keychain for development** - Keep credentials secure
2. **Use cloud stores for production** - Enable team sharing
3. **Check for missing secrets** - Validate required values
4. **Use versioning** - Maintain multiple versions for rollback
5. **Handle errors gracefully** - Provide fallback values

## Troubleshooting

### Secret Not Found

```python
# Check if secret exists
env = dotenv_values()
if "MY_KEY" not in env:
    print("MY_KEY not found in secrets")
```

### Service Not Available

```python
# Check if service is installed
try:
    load_dotenv(service="vault")
except ImportError:
    print("Vault support not installed. Install with: pip install enveloper[vault]")
```

### Permission Errors

```python
# Check credentials for cloud services
# AWS: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
# GCP: GOOGLE_CLOUD_PROJECT, ADC
# Azure: AZURE_VAULT_URL, DefaultAzureCredential