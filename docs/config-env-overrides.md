# Config and Environment Variable Overrides

## Overview

`enveloper` supports multiple ways to configure project, domain, and service settings. Values can be overridden at different levels, with a clear priority order.

## Priority Order

Configuration values are resolved in this order (highest to lowest priority):

1. **CLI arguments** (e.g., `--project myproject`)
2. **Environment variables** (e.g., `ENVELOPER_PROJECT=myproject`)
3. **Config file** (`.enveloper.toml`)
4. **Default values** (e.g., `"default"`)

## Global Options

| Option | Environment Variable | Config File | Default |
|--------|---------------------|-------------|---------|
| `--project` / `-p` | `ENVELOPER_PROJECT` | `[enveloper]` → `project` | `"default"` |
| `--domain` / `-d` | `ENVELOPER_DOMAIN` | `[enveloper.domains.<name>]` | `"default"` |
| `--service` / `-s` | `ENVELOPER_SERVICE` | `[enveloper]` → `service` | `"local"` |
| `--version` / `-v` | `ENVELOPER_VERSION` | N/A | `"1.0.0"` |

## CLI Arguments

CLI arguments have the highest priority and override all other settings.

```bash
# Override project
enveloper list --project myproject

# Override domain
enveloper list --domain prod

# Override service
enveloper list --service aws

# Override version
enveloper list --version 1.0.0

# Combine overrides
enveloper get MY_KEY --project myapp --domain prod --service aws --version 2.0.0
```

## Environment Variables

Environment variables override config file settings but are overridden by CLI arguments.

### Setting Environment Variables

**Unix/Linux/macOS (bash/zsh):**
```bash
export ENVELOPER_PROJECT=myproject
export ENVELOPER_DOMAIN=prod
export ENVELOPER_SERVICE=aws
export ENVELOPER_VERSION=1.0.0
```

**Windows (PowerShell):**
```powershell
$env:ENVELOPER_PROJECT = "myproject"
$env:ENVELOPER_DOMAIN = "prod"
$env:ENVELOPER_SERVICE = "aws"
$env:ENVELOPER_VERSION = "1.0.0"
```

**One-time use:**
```bash
ENVELOPER_PROJECT=myproject enveloper list
```

### Available Environment Variables

| Variable | Purpose |
|----------|---------|
| `ENVELOPER_PROJECT` | Default project name |
| `ENVELOPER_DOMAIN` | Default domain name |
| `ENVELOPER_SERVICE` | Default service backend |
| `ENVELOPER_VERSION` | Default version |
| `ENVELOPER_SSM_PREFIX` | SSM prefix for Lambda |
| `ENVELOPER_USE_SSM` | Use SSM in Lambda (1/0) |

## Config File (`.enveloper.toml`)

The config file provides project-level defaults. It's overridden by both CLI arguments and environment variables.

### Basic Configuration

```toml
[enveloper]
project = "myproject"
service = "local"
```

### Domain-Specific Configuration

```toml
[enveloper.domains.aws]
env_file = "/path/to/.env"
ssm_prefix = "/myproject/dev/"
```

### Service-Specific Configuration

```toml
[enveloper.aws]
profile = "default"
region = "us-west-2"
```

## Override Examples

### Example 1: Project Override

**Config file:**
```toml
[enveloper]
project = "defaultproject"
```

**CLI command:**
```bash
# Uses "otherproject" from CLI, not "defaultproject" from config
enveloper list --project otherproject
```

**Environment variable:**
```bash
# Uses "envproject" from env var
export ENVELOPER_PROJECT=envproject
enveloper list
```

### Example 2: Service Override

**Config file:**
```toml
[enveloper]
service = "local"
```

**CLI command:**
```bash
# Uses "aws" from CLI
enveloper list --service aws
```

**Environment variable:**
```bash
# Uses "vault" from env var
export ENVELOPER_SERVICE=vault
enveloper list
```

### Example 3: Domain Override

**Config file:**
```toml
[enveloper.domains.aws]
ssm_prefix = "/default/prefix/"
```

**CLI command:**
```bash
# Uses custom prefix from CLI
enveloper push --service aws --prefix /custom/prefix/
```

## SDK Usage

### Python SDK

```python
from enveloper import load_dotenv, dotenv_values

# CLI flags override everything
load_dotenv(project="cli_project")  # Uses "cli_project"

# Environment variables override config
import os
os.environ["ENVELOPER_PROJECT"] = "env_project"
load_dotenv()  # Uses "env_project"

# Config file is used when no override
load_dotenv()  # Uses value from .enveloper.toml
```

### AWS Lambda

```python
import os
from enveloper import load_dotenv

# Lambda environment variables override config
os.environ["ENVELOPER_PROJECT"] = "lambda_project"
load_dotenv()  # Uses "lambda_project"

# SSM prefix for Lambda
os.environ["ENVELOPER_SSM_PREFIX"] = "/myapp/prod/"
load_dotenv(service="aws")
```

## Best Practices

1. **Use config file for defaults** - Set project-wide defaults
2. **Use environment variables for CI/CD** - Override in pipelines
3. **Use CLI for one-off commands** - Quick overrides for testing
4. **Document overrides** - Note which method is used where
5. **Test configurations** - Verify with `enveloper service`

## Troubleshooting

### Unexpected Value

If you're getting unexpected values:

1. **Check CLI arguments** - Are you passing flags?
2. **Check environment variables** - Run `env | grep ENVELOPER`
3. **Check config file** - Run `cat .enveloper.toml`
4. **Check defaults** - What are the built-in defaults?

### Debugging

```bash
# Show current configuration
enveloper service

# Check environment variables
env | grep ENVELOPER

# Check config file
cat .enveloper.toml
```

### Common Issues

**Issue:** CLI flag not overriding config file

**Solution:** Ensure flag is placed before the command:
```bash
# Correct
enveloper --project myproject list

# Wrong (flag after command)
enveloper list --project myproject
```

**Issue:** Environment variable not being read

**Solution:** Ensure variable is exported:
```bash
# Correct
export ENVELOPER_PROJECT=myproject
enveloper list

# Wrong (not exported)
ENVELOPER_PROJECT=myproject
enveloper list