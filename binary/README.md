# Binary Build System for enveloper

This directory contains the build system for creating standalone executables of the enveloper CLI using **cx_Freeze**.

## Why cx_Freeze?

cx_Freeze provides significantly faster startup times compared to PyInstaller:

| Feature | PyInstaller | cx_Freeze |
|---------|-------------|-----------|
| Startup Time | Slow (bootloader overhead) | Fast (no extraction needed) |
| Binary Size | Smaller (compressed) | Larger (all files included) |
| Complexity | Medium | Low |
| Reliability | Medium | High |

cx_Freeze creates a directory with the executable and all dependencies, avoiding the slow extraction process that PyInstaller's `--onefile` mode requires.

## Features

- **Cross-platform support**: Builds for macOS, Linux, and Windows
- **Multiple architectures**: x86_64 and arm64 for all platforms
- **Fast startup**: No bootloader overhead, instant execution
- **Native installers**: pkg for macOS, deb/rpm for Linux, msi for Windows
- **Code signing**: Support for macOS and Windows code signing
- **GitHub Releases**: Automatic upload to GitHub Releases
- **Homebrew formula**: Generate formulas for homebrew-core installation

## Prerequisites

### Required Tools

- **Python 3.10+** (for building)
- **cx_Freeze** (automatically installed if missing)
- **GitHub CLI** (`gh`) for uploading releases
- **zip** for creating archives
- **codesign** (macOS) for code signing
- **signtool** (Windows) for code signing

### Optional Tools

- **pkgbuild/productsign** (macOS) for creating pkg installers
- **dpkg-deb** (Linux) for creating deb packages
- **rpmbuild** (Linux) for creating rpm packages
- **wix** (Windows) for creating msi installers

## Installation

### On macOS

```bash
# Install cx_Freeze
pip3 install cx-freeze

# Install GitHub CLI
brew install gh

# Install codesign tools (Xcode Command Line Tools)
xcode-select --install
```

### On Linux

```bash
# Install cx_Freeze
pip3 install cx-freeze

# Install GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Install build tools
sudo apt install zip pkg-config
```

### On Windows

```powershell
# Install Python 3.10+
# Install cx_Freeze
pip install cx-freeze

# Install GitHub CLI
winget install --id GitHub.cli

# Install WiX Toolset for MSI building
# Download from: https://wixtoolset.org/
```

## Quick Start

### Build all binaries

```bash
cd binary
make build-all
```

### Build for specific platform

```bash
# macOS only
make build-mac

# Linux only
make build-linux

# Windows only
make build-win
```

### Build for specific architecture

```bash
# macOS x86_64
make build-mac-x86

# macOS arm64
make build-mac-arm
```

### macOS DMG installer (double-click install)

A single DMG file lets users double-click to install the CLI to `/usr/local/enveloper` with a symlink at `/usr/local/bin/enveloper` so it is runnable from the terminal.

```bash
# Build Mac binaries and then create .pkg + .dmg for each architecture
make build-mac-dmg

# Or: build only arm64 and create the DMG
make build-mac-arm-dmg
```

Output (for arm64) is:

- **`dist/enveloper-<version>-macos-arm64.dmg`** — double-click to open; run the contained `.pkg` to install.
- **`dist/enveloper-<version>-macos-arm64.pkg`** — same installer, without the DMG wrapper.

After installing, `enveloper` is available in the terminal (ensure `/usr/local/bin` is on your PATH).

### Test binaries

```bash
# Test all binaries
make test

# Test specific platform
make test-mac
make test-linux
make test-win
```

### Full release

```bash
# Build, test, sign, and upload all binaries
make release
```

## Code Signing

### macOS Code Signing

1. Obtain a **Developer ID Application** certificate from Apple
2. Export as `.p12` file
3. Place in `binary/certs/mac.p12`
4. Create password file at `binary/certs/mac-cert-password.txt`

```bash
mkdir -p certs
cp /path/to/certificate.p12 certs/mac.p12
echo "your-password" > certs/mac-cert-password.txt
```

### Windows Code Signing

1. Obtain a **Code Signing Certificate** from a CA
2. Export as `.pfx` file
3. Place in `binary/certs/win.pfx`
4. Create password file at `binary/certs/win-cert-password.txt`

```bash
mkdir -p certs
cp /path/to/certificate.pfx certs/win.pfx
echo "your-password" > certs/win-cert-password.txt
```

## Homebrew Formula

To generate a Homebrew formula for homebrew-core:

```bash
# Generate formula
make homebrew

# Or manually
python homebrew.py --output ../enveloper.rb
```

The formula will be written to `../enveloper.rb`.

### Submitting to homebrew-core

1. Generate the formula using `make homebrew`
2. Submit a PR to [homebrew-core](https://github.com/Homebrew/homebrew-core)
3. Include the formula and any necessary documentation

## GitHub Releases

Binaries are automatically uploaded to GitHub Releases when running:

```bash
make release
```

### Authentication

Ensure you're logged in to GitHub CLI:

```bash
gh auth login
```

Or set the `GITHUB_TOKEN` environment variable:

```bash
export GITHUB_TOKEN=your_github_token
```

## Makefile Targets

| Target | Description |
|--------|-------------|
| `build-all` | Build for all platforms and architectures |
| `build-mac` | Build for macOS (x86_64 + arm64) |
| `build-linux` | Build for Linux (x86_64 + arm64) |
| `build-win` | Build for Windows (x86_64 + arm64) |
| `build-mac-x86` | Build for macOS x86_64 only |
| `build-mac-arm` | Build for macOS arm64 only |
| `build-mac-dmg` | Build macOS .pkg and .dmg installers (after build-mac) |
| `build-mac-arm-dmg` | Build macOS arm64 and create .dmg installer |
| `build-linux-x86` | Build for Linux x86_64 only |
| `build-linux-arm` | Build for Linux arm64 only |
| `build-win-x86` | Build for Windows x86_64 only |
| `build-win-arm` | Build for Windows arm64 only |
| `test` | Test all built binaries |
| `test-mac` | Test macOS binaries |
| `test-linux` | Test Linux binaries |
| `test-win` | Test Windows binaries |
| `sign` | Sign all binaries |
| `sign-mac` | Sign macOS binaries |
| `sign-win` | Sign Windows binaries |
| `upload` | Upload to GitHub Releases |
| `release` | Full release pipeline |
| `homebrew` | Generate Homebrew formula |
| `clean` | Clean build artifacts |
| `version` | Show current version |

## Directory Structure

```
binary/
├── Makefile              # Build system
├── README.md             # This file
├── .gitignore            # Git ignore rules
├── config.py             # Build configuration
├── build.py              # Build script
├── test.py               # Test script
├── sign.py               # Code signing script
├── upload.py             # Upload script
├── homebrew.py           # Homebrew formula generator
├── setup_cxfreeze.py     # cx_Freeze setup script
├── icon/
│   └── envelope.svg      # Icon (copied from ../media/envelope.svg by make init)
├── certs/                # Code signing certificates (gitignored)
│   ├── mac.p12
│   ├── mac-cert-password.txt
│   ├── win.pfx
│   └── win-cert-password.txt
├── build/                # Build artifacts (gitignored)
├── dist/                 # Built binaries (gitignored)
└── releases/             # Release files (gitignored)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_OWNER` | GitHub owner (default: `raminf`) |
| `GITHUB_REPO` | GitHub repository (default: `enveloper`) |
| `MAC_CERT_IDENTITY` | macOS code signing identity |
| `WIN_CERT_PATH` | Windows certificate path |

## Troubleshooting

### cx_Freeze not found

```bash
pip3 install cx-freeze
```

### GitHub CLI not found

```bash
# macOS
brew install gh

# Linux
# See installation instructions above
```

### Code signing fails

1. Verify certificate is installed in keychain (macOS)
2. Verify password is correct
3. Check certificate has proper permissions

### Build fails with missing dependencies

```bash
# Install required packages
pip3 install cx-freeze click rich pyyaml

# On Linux
sudo apt install python3-pip python3-venv
```

## License

AGPL-3.0-or-later