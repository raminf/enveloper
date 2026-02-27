# Development and Contribution

## Overview

This document covers setting up a development environment, running tests, and contributing to `enveloper`.

## Prerequisites

- Python 3.8+
- `uv` (recommended) or `pip`
- Git

## Setup

### Clone the Repository

```bash
git clone https://github.com/raminf/enveloper.git
cd enveloper
```

### Install Dependencies

Using `uv` (recommended):

```bash
uv sync --extra dev --all-extras
```

Using `pip`:

```bash
pip install -e ".[dev,aws,vault,gcp,azure,alibaba]"
```

## Development Commands

### Running Tests

```bash
# All unit tests
uv run pytest tests/ -v

# Or use the Makefile
make test

# With coverage
make test-cov
```

### Linting and Type Checking

```bash
# Run linter (Ruff)
make lint

# Run type checker (mypy)
make typecheck

# Auto-format
make format

# Run all checks
make check
```

### Building and Installing

```bash
# Build package
uv build

# Install in development mode
pip install -e ".[all]"

# Install with extras
pip install -e ".[dev,aws,vault,gcp,azure,alibaba]"
```

## Project Structure

```
enveloper/
├── src/
│   └── enveloper/
│       ├── __init__.py          # Package init
│       ├── __main__.py          # CLI entry point
│       ├── config.py            # Configuration loading
│       ├── env_file.py          # .env file handling
│       ├── resolve_store.py     # Store resolution
│       ├── sdk.py               # SDK functions
│       ├── store.py             # SecretStore base class
│       ├── util.py              # Utility functions
│       ├── cli/                 # CLI commands
│       │   ├── __init__.py
│       │   ├── clear_cmd.py
│       │   ├── crud_cmd.py
│       │   ├── export_cmd.py
│       │   ├── generate_cmd.py
│       │   ├── import_cmd.py
│       │   ├── init_cmd.py
│       │   ├── list_cmd.py
│       │   ├── push_pull_cmd.py
│       │   └── service_cmd.py
│       └── stores/              # Store plugins
│           ├── __init__.py
│           ├── keychain.py
│           ├── file_store.py
│           ├── aws_ssm.py
│           ├── github.py
│           ├── vault.py
│           ├── gcp_sm.py
│           ├── azure_kv.py
│           └── aliyun_sm.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures
│   ├── test_*.py                # Unit tests
│   └── integration/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_*.py            # Integration tests
├── docs/                        # Documentation
├── Makefile
├── pyproject.toml
└── README.md
```

## Adding a New Store

See [Adding Stores](./adding-stores.md) for detailed instructions.

## Writing Tests

### Unit Tests

Unit tests are in `tests/` and use mocked stores.

```python
import pytest
from enveloper import load_dotenv, dotenv_values


def test_load_dotenv():
    # Test with mocked keychain
    load_dotenv(project="test", domain="test")
    # Add assertions


def test_dotenv_values():
    env = dotenv_values(project="test", domain="test")
    assert isinstance(env, dict)
```

### Integration Tests

Integration tests are in `tests/integration/` and require real credentials.

```python
import pytest
from enveloper.stores.aws_ssm import AWSSSMStore


@pytest.mark.integration_aws
def test_aws_ssm_roundtrip():
    store = AWSSSMStore(prefix="test/")
    store.set("MY_KEY", "hello")
    assert store.get("MY_KEY") == "hello"
    store.delete("MY_KEY")
    assert store.get("MY_KEY") is None
```

Run integration tests with:

```bash
# AWS
ENVELOPER_TEST_AWS=1 pytest -m integration_aws tests/integration/

# GCP
ENVELOPER_TEST_GCP=1 pytest -m integration_gcp tests/integration/

# Azure
ENVELOPER_TEST_AZURE=1 pytest -m integration_azure tests/integration/

# Alibaba
ENVELOPER_TEST_ALIBABA=1 pytest -m integration_alibaba tests/integration/
```

## Code Style

### Formatting

- Use Ruff for formatting
- Line length: 130 characters
- Use double quotes for strings

### Type Hints

- Use type hints for all functions
- Use `str | None` for optional strings (Python 3.10+)

### Documentation

- Document all public functions
- Use Google-style docstrings
- Include examples for complex functions

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Update documentation if needed
6. Submit a pull request

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a tag: `git tag v0.1.0`
4. Push the tag: `git push origin v0.1.0`
5. Publish to PyPI: `make publish`

## Troubleshooting

### Test Failures

```bash
# Check Python version
python --version

# Reinstall dependencies
uv sync --reinstall --extra dev --all-extras
```

### Linting Issues

```bash
# Auto-format
make format

# Check specific file
ruff check src/enveloper/my_file.py
```

### Type Checking Issues

```bash
# Run mypy
mypy src/enveloper/

# Or use the Makefile
make typecheck