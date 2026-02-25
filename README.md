# Enveloper

Manage `.env` secrets via your system keychain with cloud store plugins.

Enveloper replaces plaintext `.env` files with secure OS keychain storage
(macOS Keychain, Linux SecretService, Windows Credential Locker) and can
push/pull secrets to cloud stores like AWS SSM Parameter Store and GitHub
Actions Secrets.

## Installation

```bash
# From PyPI
pip install enveloper

# With AWS SSM support
pip install enveloper[aws]

# Development
git clone https://github.com/raminf/enveloper.git
cd enveloper
uv sync --all-extras
```

## Quick Start

```bash
# Import your existing .env file into the keychain
enveloper import .env --domain aws

# List what's stored
enveloper list

# Export for a build (use with eval in Makefiles/scripts)
eval "$(enveloper export --domain aws)"

# Push to AWS SSM Parameter Store
enveloper push aws-ssm --domain aws --prefix /myproject/prod/

# Push to GitHub Actions Secrets
enveloper push github --domain aws

# Pull from AWS SSM into local keychain
enveloper pull aws-ssm --domain aws --prefix /myproject/prod/
```

## Concepts

### Project + Domain hierarchy

Secrets are organized by **project** (top-level namespace) and **domain**
(subsystem):

```
enveloper:myproject
  aws/TWILIO_API_SID          = ACxxxx...
  aws/AUTH0_M2M_CLIENT_SECRET = s3cr3t...
  webdash/VITE_THEME          = mytheme
```

Use `--project` / `-p` and `--domain` / `-d` flags, or configure in
`.enveloper.toml`.

### Configuration file

Place `.enveloper.toml` at your project root:

```toml
[enveloper]
project = "myproject"

[enveloper.domains.aws]
env_file = "cloud/aws/.env"
ssm_prefix = "/myproject/{env}/"

[enveloper.domains.webdash]
env_file = "webdash/.env"

[enveloper.aws]
profile = "default"
region = "us-west-2"
```

### Store plugins

Built-in stores:

| Store | Backend | Direction |
|-------|---------|-----------|
| `keychain` | OS keychain (keyring) | read/write |
| `aws-ssm` | AWS SSM Parameter Store | push/pull |
| `github` | GitHub Actions Secrets | push only |

Third-party stores register via the `enveloper.stores` entry-point group.

## CLI Reference

```
enveloper import <file> [-d DOMAIN]        Import .env file into keychain
enveloper export [-d DOMAIN] [--format]    Export to stdout (env, dotenv, json)
enveloper get <key> [-d DOMAIN]            Get a single secret
enveloper set <key> <value> [-d DOMAIN]    Set a single secret
enveloper list [-d DOMAIN]                 List keys (rich table)
enveloper rm <key> [-d DOMAIN]             Remove a single secret
enveloper clear [-d DOMAIN]                Clear all secrets

enveloper push <store> [-d DOMAIN]         Push keychain -> cloud
enveloper pull <store> [-d DOMAIN]         Pull cloud -> keychain

enveloper stores                           List available store plugins
enveloper generate codebuild-env           Generate CodeBuild buildspec YAML
```

## Makefile Integration

```makefile
# Three-tier fallback: CI env vars > enveloper > .env file
ifneq ($(CI),)
  # CI: env vars pre-set
else ifneq ($(shell command -v enveloper 2>/dev/null),)
  $(shell enveloper export -d aws --format dotenv > /tmp/.enveloper-$(USER).env 2>/dev/null)
  -include /tmp/.enveloper-$(USER).env
else ifneq (,$(wildcard .env))
  -include .env
endif
export
```

## License

MIT
