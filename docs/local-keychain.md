# Local Keychain Implementation

## Overview

The local keychain is the default storage backend for `enveloper`. It uses your operating system's native secure credential storage:

| Platform | Storage Backend |
|----------|-----------------|
| macOS | macOS Keychain |
| Linux | Secret Service (gnome-keyring, kwallet) |
| Windows | Windows Credential Locker |

## Benefits of Local Keychain

### Security
- Secrets are encrypted at rest using OS-level encryption
- Access is controlled by OS authentication (password, biometrics)
- No secrets are written to disk as plain text
- No external dependencies or network access required

### Convenience
- Single sign-on with your OS login
- Touch ID / Fingerprint support on supported devices
- Automatic unlock when you log in to your machine
- No password management required for secrets

### Privacy
- Secrets never leave your machine (unless you explicitly push to cloud)
- No third-party access to your credentials
- No subscription fees or cloud costs

## Local Keychain vs. .venv vs. Cloud

### Comparison Table

| Feature | Local Keychain | .venv (File) | Cloud Storage |
|---------|---------------|--------------|---------------|
| **Encryption** | OS-level | None (plain text) | Provider-level |
| **Access Control** | OS authentication | File permissions | IAM policies |
| **Portability** | Machine-specific | File-based | Cross-machine |
| **Backup** | OS backup | Manual | Automatic |
| **Team Sharing** | Not built-in | Manual file sharing | Built-in |
| **Cost** | Free | Free | Variable (usage-based) |
| **Network Required** | No | No | Yes |
| **Offline Use** | Yes | Yes | No |

### When to Use Each

#### Local Keychain (Default)
- **Best for:** Individual development, local builds, sensitive credentials
- **Use when:** You want maximum security with minimal setup
- **Example:** API keys, database passwords for local development

#### .venv (File)
- **Best for:** Non-sensitive configuration, CI/CD environments
- **Use when:** You need to commit configuration to version control
- **Example:** Feature flags, non-sensitive environment settings

#### Cloud Storage
- **Best for:** Team collaboration, production deployments
- **Use when:** You need to share secrets across team members
- **Example:** Production credentials, shared API keys

## Platform-Specific Details

### macOS Keychain

**How it works:**
- Uses the macOS Keychain API via the `keyring` library
- Stores secrets in the user's login keychain
- Supports Touch ID authentication

**Configuration:**
```bash
# Initialize keychain access (run once after install)
enveloper init

# This disables auto-lock for the login keychain
# First access may show an "allow keychain" dialog
# Click "Always Allow" to avoid password prompts
```

**Touch ID for sudo:**
You can configure Touch ID for `sudo` commands:
```bash
# Add to /etc/pam.d/sudo_local
auth sufficient pam_tid.so
```

### Linux Secret Service

**Supported backends:**
- `gnome-keyring` (GNOME desktop)
- `kwallet` (KDE desktop)
- `secret-service` (generic)

**Requirements:**
```bash
# Ubuntu/Debian
sudo apt install gnome-keyring

# Fedora
sudo dnf install gnome-keyring

# Arch Linux
sudo pacman -S gnome-keyring

# KDE (KWallet)
sudo apt install kwallet
```

**Configuration:**
```bash
# Initialize (checks daemon is running)
enveloper init

# Ensure your keyring is unlocked at login
# Most desktop environments handle this automatically
```

### Windows Credential Locker

**How it works:**
- Uses Windows Credential Manager API
- Stores in Windows Credential Locker
- Unlocked with your Windows session

**Configuration:**
- No additional setup required
- Windows Hello works if configured
- Credentials are encrypted with user-specific key

## Keychain Operations

### Storing a Secret
```bash
enveloper set MY_KEY my_value -d prod
```

### Retrieving a Secret
```bash
enveloper get MY_KEY -d prod
```

### Listing Secrets
```bash
enveloper list -d prod
```

### Deleting a Secret
```bash
enveloper delete MY_KEY -d prod
```

### Clearing All Secrets
```bash
enveloper clear -d prod
```

## Security Best Practices

1. **Use local keychain for development** - Keep sensitive credentials local
2. **Push to cloud only when needed** - Use `enveloper push` to share with team
3. **Enable OS-level security** - Use strong passwords, biometrics
4. **Regular backups** - Ensure your OS keychain is backed up
5. **Use versioning** - Maintain multiple versions for rollback

## Troubleshooting

### macOS Keychain Issues

**"Allow keychain" dialog appears every time:**
- Open Keychain Access
- Find the enveloper entry
- Double-click and change "Access Control" to "Allow all applications"

**Keychain is locked:**
```bash
# Unlock via command line
security unlock-keychain ~/Library/Keychains/login.keychain-db
```

### Linux Secret Service Issues

**Daemon not running:**
```bash
# Start gnome-keyring
eval $(gnome-keyring-daemon --start --components=keyring)
export SSH_AUTH_SOCK
```

**Permission denied:**
```bash
# Check keyring status
secret-tool --help

# Unlock keyring
gnome-keyring-daemon --unlock
```

### Windows Credential Locker Issues

**Credentials not found:**
- Open Windows Credential Manager
- Check under "Windows Credentials"
- Verify the enveloper entries exist

**Access denied:**
- Run as current user (not administrator)
- Check Windows Hello is configured