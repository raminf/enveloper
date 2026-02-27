# Service Backend

## Overview

The service backend determines where secrets are stored and retrieved from. `enveloper` supports multiple backends including local keychain, file storage, and various cloud services.

## Available Services

| Service | Store Class | Read/Write | Description |
|---------|-------------|------------|-------------|
| `local` | `KeychainStore` | Read/Write | OS keychain (macOS, Linux, Windows) |
| `file` | `FileStore` | Read/Write | Plain `.env` file |
| `aws` | `AWSSSMStore` | Push/Pull | AWS SSM Parameter Store |
| `github` | `GitHubStore` | Push only | GitHub Actions secrets |
| `vault` | `VaultStore` | Push/Pull | HashiCorp Vault KV v2 |
| `gcp` | `GCPSMStore` | Push/Pull | Google Cloud Secret Manager |
| `azure` | `AzureKVStore` | Push/Pull | Azure Key Vault |
| `aliyun` | `AliyunSMStore` | Push/Pull | Alibaba Cloud KMS |

## Service Selection

### CLI

```bash
# Use local keychain (default)
enveloper list --service local

# Use file storage
enveloper list --service file --path .env

# Use AWS SSM
enveloper list --service aws

# Use GitHub
enveloper list --service github
```

### Environment Variable

```bash
export ENVELOPER_SERVICE=aws
enveloper list  # Uses AWS
```

### Config File

```toml
[enveloper]
service = "aws"
```

## Service-Specific Configuration

### Local Keychain

No additional configuration required. Uses OS-native keychain storage.

### File Service

```bash
# Specify file path
enveloper list --service file --path .env.local

# Export to file
enveloper export --service file --path .env.backup
```

### AWS SSM

```toml
[enveloper.aws]
profile = "default"
region = "us-west-2"
```

```bash
# Push to SSM
enveloper push --service aws -d prod --prefix /myapp/prod/

# Pull from SSM
enveloper pull --service aws -d prod --prefix /myapp/prod/
```

### GitHub

```bash
# Push to GitHub Actions
enveloper push --service github -d prod --repo owner/repo
```

### HashiCorp Vault

```toml
[enveloper.vault]
url = "http://127.0.0.1:8200"
mount = "secret"
```

```bash
# Push to Vault
enveloper push --service vault -d prod --prefix myapp/prod

# Pull from Vault
enveloper pull --service vault -d prod --prefix myapp/prod
```

### Google Cloud

```toml
[enveloper.gcp]
project = "my-gcp-project"
```

```bash
# Push to Secret Manager
enveloper push --service gcp -d prod --prefix myapp-prod

# Pull from Secret Manager
enveloper pull --service gcp -d prod --prefix myapp-prod
```

### Azure Key Vault

```toml
[enveloper.azure]
vault_url = "https://my-vault.vault.azure.net/"
```

```bash
# Push to Key Vault
enveloper push --service azure -d prod --prefix myapp-prod

# Pull from Key Vault
enveloper pull --service azure -d prod --prefix myapp-prod
```

### Alibaba Cloud

```toml
[enveloper.aliyun]
region_id = "cn-hangzhou"
access_key_id = "..."
access_key_secret = "..."
```

```bash
# Push to KMS
enveloper push --service aliyun -d prod --prefix myapp-prod

# Pull from KMS
enveloper pull --service aliyun -d prod --prefix myapp-prod
```

## Service Commands

### List Services

```bash
# List all available services
enveloper service

# List store plugins
enveloper stores
```

### Push/Pull

```bash
# Push from local to cloud
enveloper push --service aws -d prod

# Pull from cloud to local
enveloper pull --service aws -d prod

# Push from file to cloud
enveloper push --service aws --from file --path .env

# Pull from cloud to file
enveloper pull --service aws --to file --path .env
```

### Clear Service

```bash
# Clear local keychain
enveloper clear --service local -d prod

# Clear file
enveloper clear --service file --path .env

# Clear cloud store
enveloper clear --service aws -d prod
```

## Service Backend Selection Matrix

| Use Case | Recommended Service |
|----------|---------------------|
| Local development | `local` (keychain) |
| CI/CD with .env files | `file` |
| AWS infrastructure | `aws` (SSM) |
| GitHub Actions | `github` |
| Multi-cloud | `vault` |
| GCP infrastructure | `gcp` |
| Azure infrastructure | `azure` |
| Alibaba infrastructure | `aliyun` |

## Service Priority

When no service is specified, `enveloper` uses `local` as the default. You can change this default:

1. **Config file** (`.enveloper.toml`):
   ```toml
   [enveloper]
   service = "aws"
   ```

2. **Environment variable**:
   ```bash
   export ENVELOPER_SERVICE=aws
   ```

3. **CLI argument** (highest priority):
   ```bash
   enveloper list --service aws
   ```

## Troubleshooting

### Service Not Found

```bash
# Check available services
enveloper service

# Verify service name
enveloper --service aws list
```

### Permission Denied

Check service-specific credentials:
- **AWS**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- **GCP**: `GOOGLE_CLOUD_PROJECT`, Application Default Credentials
- **Azure**: `AZURE_VAULT_URL`, DefaultAzureCredential
- **Vault**: `VAULT_ADDR`, `VAULT_TOKEN`

### Connection Issues

```bash
# Test connection
enveloper service

# Check network connectivity
ping <service-endpoint>