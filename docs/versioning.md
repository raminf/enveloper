# Versioning

## Overview

`enveloper` supports semantic versioning (semver) for secrets, allowing you to maintain multiple versions of your configuration for different environments or deployments.

## Version Format

Versions follow [semver](https://semver.org/) format: `MAJOR.MINOR.PATCH`

Examples:
- `1.0.0` - Initial stable release
- `2.1.3` - Major version 2, minor version 1, patch 3
- `0.2.5` - Early development version

## CLI Usage

### Setting a Secret with Version

```bash
enveloper set MY_KEY value -d prod -v 1.0.0
enveloper set MY_KEY value -d prod -v 2.0.0
```

### Getting a Secret with Version

```bash
enveloper get MY_KEY -d prod -v 1.0.0
enveloper get MY_KEY -d prod -v 2.0.0
```

### Listing Secrets with Version

```bash
enveloper list -d prod -v 1.0.0
enveloper list -d prod -v 2.0.0
```

### Import with Version

```bash
enveloper import .env -d prod -v 1.0.0
enveloper import .env -d prod -v 2.0.0
```

### Export with Version

```bash
enveloper export -d prod -v 1.0.0 --format dotenv -o v1.env
enveloper export -d prod -v 2.0.0 --format dotenv -o v2.env
```

## Version Environment Variable

Set `ENVELOPER_VERSION` to use a default version:

```bash
export ENVELOPER_VERSION=1.0.0
enveloper list -d prod  # Uses version 1.0.0
```

## SDK Usage

### load_dotenv with Version

```python
from enveloper import load_dotenv

# Load secrets with a specific version
load_dotenv(project="myapp", domain="prod", version="1.0.0")
load_dotenv(project="myapp", domain="prod", version="2.0.0")
```

### dotenv_values with Version

```python
from enveloper import dotenv_values

# Get secrets with a specific version
env = dotenv_values(project="myapp", domain="prod", version="1.0.0")
db_url = env.get("DATABASE_URL")

# Compare versions
v1 = dotenv_values(project="myapp", domain="prod", version="1.0.0")
v2 = dotenv_values(project="myapp", domain="prod", version="2.0.0")
```

## Versioning Use Cases

### Environment Separation

Maintain separate versions for different environments:

```
myapp/prod/1.0.0/DB_PASSWORD
myapp/staging/1.0.0/DB_PASSWORD
myapp/dev/1.0.0/DB_PASSWORD
```

### Rollback Support

Keep previous versions for quick rollback:

```bash
# Current version
enveloper set DB_PASSWORD newpass -d prod -v 2.0.0

# Previous version still available
enveloper get DB_PASSWORD -d prod -v 1.0.0
```

### Feature Flags

Version feature flags with code:

```
feature/v1.0.0/NEW_UI_ENABLED=true
feature/v2.0.0/NEW_UI_ENABLED=false
```

### Database Schema Versions

Match database schema versions:

```
db/v1.0.0/MIGRATION_VERSION=1
db/v2.0.0/MIGRATION_VERSION=2
```

## Cloud Store Versioning

Different cloud stores handle versioning differently:

| Service | Version Separator | Notes |
|---------|-------------------|-------|
| AWS SSM | `/` | Uses path hierarchy |
| GitHub | `_` | Underscore for compatibility |
| Vault | `/` | Path-based |
| GCP | `--` | Hyphen separator |
| Azure | `--` | Hyphen separator |
| Alibaba | `--` | Hyphen separator |

## Best Practices

1. **Use consistent versioning** - Follow semver strictly
2. **Document changes** - Update version when secrets change
3. **Keep old versions** - Don't delete immediately for rollback
4. **Test version switching** - Verify version changes work
5. **Automate version bumps** - Use CI/CD for version management

## Migration Between Versions

### Manual Migration

```bash
# Export old version
enveloper export -d prod -v 1.0.0 --format json -o v1.json

# Import to new version
enveloper import v1.json -d prod -v 2.0.0
```

### Programmatic Migration

```python
from enveloper import dotenv_values, load_dotenv

# Load from old version
old_env = dotenv_values(project="myapp", domain="prod", version="1.0.0")

# Process and update
new_env = {k: v for k, v in old_env.items() if not k.startswith("OLD_")}

# Save to new version
# (requires manual set operations)
```

## Troubleshooting

### Version Not Found

```bash
# Check available versions by listing without version filter
enveloper list -d prod

# Verify version format (must be semver: MAJOR.MINOR.PATCH)
```

### Version Conflicts

If multiple versions exist, specify the version explicitly:

```bash
enveloper get MY_KEY -d prod -v 1.0.0
```

### SDK Version Issues

Ensure version is passed correctly:

```python
# Correct
load_dotenv(version="1.0.0")

# Not this (version is not an env var)
load_dotenv()  # Uses ENVELOPER_VERSION env var if set