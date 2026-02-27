# Technical Details

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         enveloper CLI/SDK                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
            ┌───────▼───────┐ ┌────▼──────┐ ┌─────▼──────┐
            │   Local       │ │  File   │ │  Cloud     │
            │   Keychain    │ │  Store  │ │  Stores    │
            │  (OS native)  │ │  (.env) │ │  (plugins) │
            └───────────────┘ └─────────┘ └────────────┘
                    │               │               │
            ┌───────▼───────┐ ┌────▼──────┐ ┌─────▼──────┐
            │ macOS         │ │  Plain  │ │  AWS SSM   │
            │ Linux         │ │  .env   │ │  GitHub    │
            │ Windows       │ │  files  │ │  Vault     │
            └───────────────┘ └─────────┘ │  GCP       │
                                          │  Azure       │
                                          │  Alibaba     │
                                          └────────────┘
```

## Key Composition

Every secret is stored under a composite key built from five segments:

```
{prefix}{sep}{domain}{sep}{project}{sep}{version}{sep}{name}
```

| Segment | Default | Source |
|---------|---------|--------|
| `prefix` | `envr` | `SecretStore.prefix` class attr |
| `sep` | `/` | `SecretStore.key_separator` |
| `domain` | `_default_` | CLI `--domain` / env var |
| `project` | `_default_` | CLI `--project` / config |
| `version` | `1.0.0` | CLI `--version` / env var |
| `name` | *(user-supplied)* | The actual secret name |

**Example:** With AWS store (separator `/`), the key for `API_KEY` might be:
```
/envr/payments/myapp/1.0.0/API_KEY
```

## SecretStore Interface

All store plugins inherit from `SecretStore` (defined in `src/enveloper/store.py`).

### Required Class Attributes

| Attribute | Purpose |
|-----------|---------|
| `service_name` | Short CLI name (e.g., `"aws"`, `"file"`) |
| `service_display_name` | Human-readable description |
| `service_doc_url` | Documentation URL (optional) |

### Abstract Methods

```python
def get(self, key: str) -> str | None: ...
def set(self, key: str, value: str) -> None: ...
def delete(self, key: str) -> None: ...
def list_keys(self) -> list[str]: ...
```

### Provided Methods

| Method | Description |
|--------|-------------|
| `clear()` | Deletes every key from `list_keys()` |
| `build_key(name, project, domain, version)` | Builds composite key string |
| `parse_key(key)` | Splits composite key into segments |
| `key_to_export_name(key)` | Extracts name from composite key |
| `sanitize_key_segment(value)` | Replaces separator with `_` |

## Entry Point System

Stores are discovered via Python entry points defined in `pyproject.toml`:

```toml
[project.entry-points."enveloper.stores"]
keychain = "enveloper.stores.keychain:KeychainStore"
aws = "enveloper.stores.aws_ssm:AWSSSMStore"
github = "enveloper.stores.github:GitHubStore"
vault = "enveloper.stores.vault:VaultStore"
gcp = "enveloper.stores.gcp_sm:GCPSMStore"
azure = "enveloper.stores.azure_kv:AzureKVStore"
aliyun = "enveloper.stores.aliyun_sm:AliyunSMStore"
file = "enveloper.stores.file_store:FileStore"
```

## Configuration Loading

Configuration is loaded in this priority order:

1. **CLI arguments** (highest priority)
2. **Environment variables**
3. **Config file** (`.enveloper.toml`)
4. **Default values** (lowest priority)

## Environment Variable Resolution

For each setting, the CLI checks:

1. Command-line flag (e.g., `--domain prod`)
2. Environment variable (e.g., `ENVELOPER_DOMAIN=prod`)
3. Config file value (e.g., `[enveloper] domain = "prod"`)
4. Default value (e.g., `"default"`)

## Service Backend Selection

The `--service` flag determines which backend to use:

| Service | Store Class | Description |
|---------|-------------|-------------|
| `local` | `KeychainStore` | OS keychain |
| `file` | `FileStore` | Plain `.env` file |
| `aws` | `AWSSSMStore` | AWS SSM Parameter Store |
| `github` | `GitHubStore` | GitHub Actions secrets |
| `vault` | `VaultStore` | HashiCorp Vault KV v2 |
| `gcp` | `GCPSMStore` | Google Cloud Secret Manager |
| `azure` | `AzureKVStore` | Azure Key Vault |
| `aliyun` | `AliyunSMStore` | Alibaba Cloud KMS |

## Versioning

Versions follow [semver](https://semver.org/) format: `MAJOR.MINOR.PATCH`

Cloud stores may use different separators internally:
- GitHub uses `_` instead of `.` for version compatibility
- AWS SSM uses `/` as path separator

## Import/Export Formats

### dotenv
```
KEY=value
ANOTHER_KEY=another_value
```

### unix (for shell)
```bash
export KEY=value
export ANOTHER_KEY=another_value
```

### win (PowerShell)
```powershell
$env:KEY = 'value'
$env:ANOTHER_KEY = 'another_value'
```

### JSON
```json
{
  "KEY": "value",
  "ANOTHER_KEY": "another_value"
}
```

### YAML
```yaml
KEY: value
ANOTHER_KEY: another_value
```

## Error Handling

Errors are handled with specific exit codes:
- `0` - Success
- `1` - General error
- `2` - Invalid arguments
- `3` - Configuration error
- `4` - Authentication/permission error