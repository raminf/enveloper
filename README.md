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

## Platform Setup

After installing, run `enveloper init` to configure your OS keychain for
frictionless access:

```bash
enveloper init
```

### macOS

- **Keychain auto-lock**: `init` disables auto-lock on the login keychain so
  it stays unlocked while you're logged in.
- **First access dialog**: macOS shows an "allow this application to access
  keychain item?" dialog the first time Python reads each secret. Click
  **Always Allow** to permanently authorize. If you change Python venvs or
  upgrade Python, the dialog appears once more (macOS tracks the binary path).
- **Touch ID for sudo**: If your Mac has Touch ID, `init` shows how to enable
  Touch ID for `sudo` commands (useful for build steps that need elevated
  privileges). Add to `/etc/pam.d/sudo_local`:
  ```
  auth       sufficient     pam_tid.so
  ```

### Linux

- GNOME Keyring and KDE Wallet auto-unlock at login. No password prompts
  during builds.
- `init` checks that a Secret Service daemon is running. If not, install
  `gnome-keyring` or `kwallet` and ensure it starts at login.

### Windows

- Windows Credential Locker is unlocked with your user session. No additional
  setup needed.
- If Windows Hello (fingerprint/face) is configured for login, credentials
  are available after biometric unlock.

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
enveloper init                             Configure OS keychain for frictionless access
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
