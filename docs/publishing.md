# Publishing to PyPI

## Overview

This document covers the process of publishing `enveloper` to PyPI and TestPyPI.

## Prerequisites

- `twine` installed: `pip install twine`
- PyPI account with 2FA enabled
- API token for PyPI
- API token for TestPyPI (optional)

## Configuration

### Create `~/.pypirc`

```ini
[pypi]
username = __token__
password = pypi-...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-...
```

### Get API Tokens

- [PyPI](https://pypi.org/manage/account/token/)
- [TestPyPI](https://test.pypi.org/manage/account/token/)

## Using Make

### Publish to TestPyPI

```bash
make publish-test
```

This command:
1. Bumps the patch version
2. Builds the package
3. Uploads to TestPyPI

### Publish to PyPI

```bash
make publish
```

This command:
1. Builds the package
2. Uploads to PyPI

## Manual Publishing

### Build the Package

```bash
uv build
```

### Upload to TestPyPI

```bash
uv run twine upload -r testpypi dist/*
```

### Upload to PyPI

```bash
uv run twine upload dist/*
```

## GitHub Actions (Optional)

The repo includes a workflow that publishes **only** on version tags or when you run it manually.

### Setup

1. Configure [trusted publishing](https://docs.pypi.org/trusted-publishers/) on PyPI and TestPyPI
2. Create GitHub Environments `pypi` and `testpypi`
3. See the comments in [`.github/workflows/publish.yml`](https://github.com/raminf/enveloper/blob/main/.github/workflows/publish.yml)

### Usage

1. Push a tag like `v0.1.9` (matching `version` in `pyproject.toml`)
2. Or use **Actions → Publish to PyPI → Run workflow** and choose PyPI or TestPyPI

## Versioning

Versions are managed in `pyproject.toml`:

```toml
[project]
version = "0.1.9"
```

The `make publish-test` command automatically bumps the patch version.

## Verification

### TestPyPI

```bash
# Install from TestPyPI
pip install -i https://test.pypi.org/simple/ enveloper

# Verify installation
enveloper --version
```

### PyPI

```bash
# Install from PyPI
pip install enveloper

# Verify installation
enveloper --version
```

## Troubleshooting

### Authentication Failed

```bash
# Check ~/.pypirc
cat ~/.pypirc

# Verify token is valid
curl -u __token__:pypi-... https://upload.pypi.org/legacy/
```

### File Already Exists

```bash
# TestPyPI allows overwriting, PyPI does not
# For PyPI, bump the version first
```

### Build Errors

```bash
# Clean build directory
rm -rf dist/ build/ *.egg-info

# Rebuild
uv build
```

### Upload Errors

```bash
# Check file permissions
ls -la dist/

# Verify file integrity
twine check dist/*