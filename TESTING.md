# Testing

This document describes how to run the test suite and how to enable and configure integration tests for individual cloud services.

## Overview

- **Unit tests** (in `tests/`) run by default and do not require cloud credentials. They use a mocked keychain and exercise the CLI, SDK, stores, and utilities.
- **Integration tests** (in `tests/integration/`) hit real cloud APIs and are **disabled by default**. You enable them with environment variables and pytest markers.

## Linting and type-checking

Lint (Ruff) and type-check (mypy) run in CI and are required before release. Run them locally with:

```bash
make lint        # Ruff: check src/ and tests/
make typecheck   # mypy: package + tests
make format      # Ruff: auto-format
make check       # lint + typecheck + test (CI gate)
```

- **Ruff** config: `[tool.ruff]` in `pyproject.toml` (line-length 130, select E/F/I/W).
- **mypy** config: `[tool.mypy]` in `pyproject.toml`; optional/store modules use `ignore_missing_imports` and some overrides.

## Running tests

```bash
# All unit tests (default)
uv run pytest tests/ -v

# Or use the Makefile
make test

# With coverage
make test-cov
# or: uv run pytest tests/ -v --cov=enveloper --cov-report=term-missing
```

Integration tests are skipped unless you set the appropriate env vars and pass the matching marker (see below).

## Unit test fixtures

- **`mock_keyring`** (in `tests/conftest.py`): Replaces the real keyring backend with an in-memory dict so tests can run without touching the OS keychain. The fixture returns the backing dict for inspection.
- **`sample_env`**: Provides a temporary `.env` file with sample key/value pairs for import/export tests.

## Enabling and configuring cloud integration tests

Install the extra(s) for the cloud provider(s) you want to test, then set the required environment variables and run with the corresponding pytest marker.

### AWS (SSM Parameter Store)

- **Extra:** `enveloper[aws]`
- **Marker:** `integration_aws`
- **Environment:**
  - `ENVELOPER_TEST_AWS=1` — required to enable tests
  - `ENVELOPER_TEST_AWS_PREFIX` — optional; SSM parameter prefix (default: `/enveloper-integration-test/`)
- **Credentials:** Standard AWS (env vars `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`, or `AWS_PROFILE`, or IAM role)

```bash
pip install enveloper[aws]
export ENVELOPER_TEST_AWS=1
export ENVELOPER_TEST_AWS_PREFIX=/enveloper-integration-test/   # optional
pytest -m integration_aws tests/integration/test_aws_ssm.py -v
```

### Google Cloud (Secret Manager)

- **Extra:** `enveloper[gcp]`
- **Marker:** `integration_gcp`
- **Environment:**
  - `ENVELOPER_TEST_GCP=1` — required to enable tests
  - `ENVELOPER_TEST_GCP_PROJECT` — required; your GCP project ID
- **Credentials:** Application Default Credentials (e.g. `gcloud auth application-default login`) or service account env vars

```bash
pip install enveloper[gcp]
export ENVELOPER_TEST_GCP=1
export ENVELOPER_TEST_GCP_PROJECT=your-gcp-project-id
pytest -m integration_gcp tests/integration/test_gcp_sm.py -v
```

### Azure (Key Vault)

- **Extra:** `enveloper[azure]`
- **Marker:** `integration_azure`
- **Environment:**
  - `ENVELOPER_TEST_AZURE=1` — required to enable tests
  - `ENVELOPER_TEST_AZURE_VAULT_URL` — required; Key Vault URL (e.g. `https://your-vault.vault.azure.net/`)
- **Credentials:** DefaultAzureCredential (Azure CLI login, env vars, or managed identity)

```bash
pip install enveloper[azure]
export ENVELOPER_TEST_AZURE=1
export ENVELOPER_TEST_AZURE_VAULT_URL=https://your-vault.vault.azure.net/
pytest -m integration_azure tests/integration/test_azure_kv.py -v
```

### Alibaba Cloud (KMS Secrets Manager)

- **Extra:** `enveloper[alibaba]`
- **Marker:** `integration_alibaba`
- **Environment:**
  - `ENVELOPER_TEST_ALIBABA=1` — required to enable tests
  - `ENVELOPER_TEST_ALIBABA_REGION` — optional; default `cn-hangzhou`
  - `ALIBABA_CLOUD_ACCESS_KEY_ID` — required for credentials
  - `ALIBABA_CLOUD_ACCESS_KEY_SECRET` — required for credentials
- **Credentials:** Access key ID and secret in env (as above) or Alibaba config

```bash
pip install enveloper[alibaba]
export ENVELOPER_TEST_ALIBABA=1
export ENVELOPER_TEST_ALIBABA_REGION=cn-hangzhou   # optional
export ALIBABA_CLOUD_ACCESS_KEY_ID=your-key-id
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=your-secret
pytest -m integration_alibaba tests/integration/test_aliyun_sm.py -v
```

## Running all integration tests

With all extras and credentials configured, you can run every integration suite:

```bash
uv sync --all-extras
# Set env vars for each provider you want to test, then:
pytest -m "integration_aws or integration_gcp or integration_azure or integration_alibaba" tests/integration/ -v
```

Or run one provider at a time as in the examples above.

## Pytest markers

Markers are defined in `pyproject.toml` under `[tool.pytest.ini_options]`:

| Marker              | Description |
|---------------------|-------------|
| `integration_aws`   | AWS SSM integration tests |
| `integration_gcp`   | GCP Secret Manager integration tests |
| `integration_azure` | Azure Key Vault integration tests |
| `integration_alibaba` | Alibaba Cloud KMS Secrets integration tests |

Integration tests are skipped if the corresponding enable env var is not set, so you can pass the marker and only the configured providers will run; others will skip with a message indicating which variable to set.
