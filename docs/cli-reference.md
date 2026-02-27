# CLI Reference

The `enveloper` CLI (also available as `envr`) provides commands for managing secrets across local keychain and cloud stores.

## Global Options

These options can be used before any command:

| Option | Environment Variable | Config File | Default |
|--------|---------------------|-------------|---------|
| `--project` / `-p` | `ENVELOPER_PROJECT` | `[enveloper]` → `project` | `"default"` |
| `--domain` / `-d` | `ENVELOPER_DOMAIN` | `[enveloper.domains.<name>]` | `"default"` |
| `--service` / `-s` | `ENVELOPER_SERVICE` | `[enveloper]` → `service` | `"local"` |
| `--path` | N/A | N/A | `.env` (for file service) |
| `--version` / `-v` | `ENVELOPER_VERSION` | N/A | `"1.0.0"` |
| `--prefix` | N/A | N/A | Auto-generated from domain/project |

## Commands

### `enveloper init`

Configure OS keychain for frictionless access.

- **macOS**: Disables login keychain auto-lock
- **Linux**: Checks that gnome-keyring or kwallet daemon is running
- **Windows**: No action needed (Credential Locker unlocked with session)

### `enveloper import <file>`

Import secrets from a file into the current service.

**Options:**
- `-d, --domain DOMAIN` - Domain name
- `-s, --service SERVICE` - Service backend (default: local)
- `--path PATH` - File path (for file service)
- `--format FORMAT` - Input format: `env` (default), `json`, `yaml`

**Examples:**
```bash
enveloper import .env -d prod
enveloper import secrets.json --format json -d dev
enveloper import .env --service file --path .env.local
```

### `enveloper export`

Export secrets from the current service.

**Options:**
- `-d, --domain DOMAIN` - Domain name
- `-s, --service SERVICE` - Service backend (default: local)
- `--path PATH` - File path (for file service)
- `--format FORMAT` - Output format: `dotenv` (default), `unix`, `win`, `json`, `yaml`
- `-o, --output FILE` - Write to file instead of stdout

**Examples:**
```bash
# Export for shell (use with eval)
eval "$(enveloper export -d prod --format unix)"

# Export to .env file
enveloper export -d prod -o backup.env

# Export to JSON
enveloper export -d prod --format json -o secrets.json

# Windows PowerShell
enveloper export -d prod --format win | Invoke-Expression
```

### `enveloper unexport`

Output unset commands to clear environment variables.

**Options:**
- `-d, --domain DOMAIN` - Domain name
- `-s, --service SERVICE` - Service backend
- `--path PATH` - File path
- `--format FORMAT` - Output format: `unix`, `win`

### `enveloper get <key>`

Get a single secret value.

**Options:**
- `-d, --domain DOMAIN` - Domain name
- `-s, --service SERVICE` - Service backend
- `--path PATH` - File path

### `enveloper set <key> <value>`

Set a single secret value.

**Options:**
- `-d, --domain DOMAIN` - Domain name
- `-s, --service SERVICE` - Service backend
- `--path PATH` - File path

### `enveloper list`

List all secrets in the current project/domain.

**Options:**
- `-d, --domain DOMAIN` - Domain name
- `-s, --service SERVICE` - Service backend
- `--path PATH` - File path

Output is a table with masked values.

### `enveloper delete <key>`

Remove a single secret.

**Options:**
- `-d, --domain DOMAIN` - Domain name
- `-s, --service SERVICE` - Service backend
- `--path PATH` - File path

### `enveloper clear`

Clear all secrets from the current service.

**Options:**
- `-d, --domain DOMAIN` - Domain name
- `-s, --service SERVICE` - Service backend
- `--path PATH` - File path
- `-q, --quiet` - Skip confirmation prompt

**Warning:** This is NOT REVERSIBLE. Use `enveloper export -o backup.env` first to create a backup.

### `enveloper push`

Push secrets to a cloud store.

**Options:**
- `--service STORE` - Cloud store (aws, github, vault, gcp, azure, aliyun)
- `--from SOURCE` - Source backend (local, file; default: local)
- `-d, --domain DOMAIN` - Domain name
- `--path PATH` - File path
- `--prefix PREFIX` - Cloud store prefix/path

**Examples:**
```bash
# Push to AWS SSM
enveloper push --service aws -d prod --prefix /myapp/prod/

# Push to GitHub Actions
enveloper push --service github -d prod --repo owner/repo

# Push from file to cloud
enveloper push --service aws --from file --path .env
```

### `enveloper pull`

Pull secrets from a cloud store.

**Options:**
- `--service STORE` - Cloud store (aws, github, vault, gcp, azure, aliyun)
- `--to TARGET` - Target backend (local, file; default: local)
- `-d, --domain DOMAIN` - Domain name
- `--path PATH` - File path
- `--prefix PREFIX` - Cloud store prefix/path

**Examples:**
```bash
# Pull from AWS SSM
enveloper pull --service aws -d prod --prefix /myapp/prod/

# Pull to file
enveloper pull --service aws --to file --path .env
```

### `enveloper service`

List all available service providers with descriptions and documentation links.

### `enveloper stores`

List all available store plugins.

### `enveloper generate codebuild-env`

Generate AWS CodeBuild buildspec YAML snippet.

**Options:**
- `-d, --domain DOMAIN` - Domain name
- `--prefix PREFIX` - SSM parameter prefix

## Format Options

### Export Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `dotenv` | `KEY=value` | `.env` files, general use |
| `unix` | `export KEY=value` | Bash/Zsh shells |
| `win` | `$env:KEY = 'value'` | PowerShell |
| `json` | `{"KEY": "value"}` | Docker, CDK, config files |
| `yaml` | `KEY: value` | Docker, Kubernetes, config files |

### Import Formats

| Format | Description |
|--------|-------------|
| `env` | `KEY=value` (default) |
| `json` | `{"KEY": "value"}` |
| `yaml` | `KEY: value` |

## Service Backends

| Service | Read/Write | Description |
|---------|-----------|-------------|
| `local` | Read/Write | OS keychain (macOS, Linux, Windows) |
| `file` | Read/Write | Plain `.env` file |
| `aws` | Push/Pull | AWS SSM Parameter Store |
| `github` | Push only | GitHub Actions secrets |
| `vault` | Push/Pull | HashiCorp Vault KV v2 |
| `gcp` | Push/Pull | Google Cloud Secret Manager |
| `azure` | Push/Pull | Azure Key Vault |
| `aliyun` | Push/Pull | Alibaba Cloud KMS Secrets Manager |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `ENVELOPER_PROJECT` | Default project name |
| `ENVELOPER_DOMAIN` | Default domain name |
| `ENVELOPER_SERVICE` | Default service backend |
| `ENVELOPER_VERSION` | Default version |
| `ENVELOPER_SSM_PREFIX` | SSM prefix for Lambda |
| `ENVELOPER_USE_SSM` | Use SSM in Lambda (1/0) |

## Config File (`.enveloper.toml`)

See [Project Config File](./project-config.md) for details.