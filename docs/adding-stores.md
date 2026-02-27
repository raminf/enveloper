# Adding Stores

## Overview

`enveloper` uses a plugin system based on Python entry points to discover and load store implementations. This document explains how to create new store plugins.

## Key Composition

Every secret is stored under a composite key built from five segments:

```
{prefix}{sep}{domain}{sep}{project}{sep}{version}{sep}{name}
```

| Segment | Default | Source |
|---------|---------|--------|
| `prefix` | `envr` | `SecretStore.prefix` class attr |
| `sep` | `/` | `SecretStore.key_separator` |
| `domain` | `_default_` | CLI `--domain` / env var |
| `project` | `_default_` | CLI `--project` / config |
| `version` | `1.0.0` | CLI `--version` |
| `name` | *(user-supplied)* | The actual secret name |

**Example:** With AWS store (separator `/`), the key for `API_KEY` might be:
```
/envr/payments/myapp/1.0.0/API_KEY
```

## The `SecretStore` Base Class

All store plugins inherit from `SecretStore` (defined in `src/enveloper/store.py`).

### Class Attributes (defaults defined on the base class)

These **only** need to be overridden if the store cannot use the base-class defaults:

| Attribute | Base Default | Purpose |
|-----------|--------------|---------|
| `default_namespace` | `"_default_"` | Used when project or domain are not supplied |
| `prefix` | `"envr"` | Namespace prefix for all keys |
| `key_separator` | `"/"` | Separates path segments (`/` for AWS, `--` for GCP) |
| `version_separator` | `"."` | Separates version digits (`"_"` when dots are banned) |

### Abstract Methods (must implement)

```python
def get(self, key: str) -> str | None: ...
def set(self, key: str, value: str) -> None: ...
def delete(self, key: str) -> None: ...
def list_keys(self) -> list[str]: ...
```

### Provided Methods (inherited, can be overridden)

| Method | What it does |
|--------|--------------|
| `clear()` | Deletes every key from `list_keys()`. Override for bulk-delete. |
| `build_key(name, project, domain, version)` | Builds the composite key string using the class attributes above. |
| `parse_key(key)` | Splits a composite key back into `{prefix, domain, project, version, name}`. |
| `key_to_export_name(key)` | Extracts just the `name` from a composite key (for `.env` export). |
| `sanitize_key_segment(value)` | Replaces the `key_separator` character in a segment with `_`. |

### Service listing (for `enveloper service`)

Every store **must** define these class attributes so it appears correctly in `enveloper service`:

| Attribute | Purpose |
|-----------|---------|
| `service_name` | Short CLI name (e.g., `"aws"`, `"file"`). Shown in the Service column. |
| `service_display_name` | Human-readable description (e.g., "AWS Systems Manager Parameter Store"). |
| `service_doc_url` | Documentation URL (optional but recommended). Rendered as "Doc Link". |

Base defaults are empty strings; subclasses must set them.

Stores that need **multiple rows** in the service table (e.g., local keychain per OS) should override:

```python
@classmethod
def get_service_rows(cls) -> list[tuple[str, str, str]]:
    """Return one or more (short_name, display_name, doc_url)."""
    return [
        ("local (MacOS)", "macOS Keychain", "https://..."),
        ("local (Windows)", "Windows Credential Locker", "https://..."),
        # ...
    ]
```

### Configuration Hook

```python
@classmethod
def build_default_prefix(cls, domain: str, project: str) -> str:
    """Return the default prefix/path for this store.
    Called when no explicit --prefix is provided."""
```

```python
@classmethod
def from_config(cls, domain, project, config, prefix=None, env_name=None, **kwargs):
    """Create an instance from CLI/config values.
    Base implementation calls build_default_prefix when prefix is None,
    then passes prefix, domain, project, and **kwargs to __init__."""
```

## Creating a New Store Plugin

### Step 1: Fork and Clone

```bash
git clone https://github.com/<you>/enveloper.git
cd enveloper
uv sync --extra dev --all-extras
```

### Step 2: Create the Store Module

Add a new file under `src/enveloper/stores/`, for example `src/enveloper/stores/my_backend.py`:

```python
from __future__ import annotations

from enveloper.store import DEFAULT_NAMESPACE, DEFAULT_PREFIX, DEFAULT_VERSION, SecretStore


class MyBackendStore(SecretStore):
    """Example store -- replace with your real backend."""

    # Required for ``enveloper service`` listing
    service_name: str = "my_backend"
    service_display_name: str = "My Backend Description"
    service_doc_url: str = "https://docs.example.com/my-backend"

    # Only override if the defaults won't work for your backend:
    # key_separator: str = "--"       # if "/" is invalid
    # version_separator: str = "_"    # if "." is invalid in key names

    @classmethod
    def build_default_prefix(cls, domain: str, project: str) -> str:
        d = cls.sanitize_key_segment(domain)
        p = cls.sanitize_key_segment(project)
        return f"{cls.prefix}{cls.key_separator}{d}{cls.key_separator}{p}"

    def __init__(
        self,
        prefix: str = "",
        version: str = DEFAULT_VERSION,
        domain: str = DEFAULT_NAMESPACE,
        project: str = DEFAULT_NAMESPACE,
        **kwargs: object,
    ) -> None:
        self._prefix = prefix
        self._version = version
        self._domain = domain
        self._project = project
        # Set up your backend client here

    def _resolve_key(self, key: str) -> str:
        """If key is already a composite key, return as-is; otherwise build one."""
        if self.parse_key(key) is not None:
            return key
        return self.build_key(
            name=key, project=self._project,
            domain=self._domain, version=self._version,
        )

    def get(self, key: str) -> str | None:
        full = self._resolve_key(key)
        # ... fetch from backend ...
        return None

    def set(self, key: str, value: str) -> None:
        full = self._resolve_key(key)
        # ... write to backend ...

    def delete(self, key: str) -> None:
        full = self._resolve_key(key)
        # ... delete from backend ...

    def list_keys(self) -> list[str]:
        # Return full composite keys so get(key) works on them
        return []
```

### Step 3: Register the Entry Point

Add to `pyproject.toml`:

```toml
[project.entry-points."enveloper.stores"]
# ... existing stores ...
my_backend = "enveloper.stores.my_backend:MyBackendStore"
```

### Step 4: Install and Test

With `service_name`, `service_display_name`, and `service_doc_url` set on your store class, it will appear in `enveloper service` automatically (no CLI changes needed).

```bash
uv sync
uv run enveloper stores          # should show my_backend
uv run enveloper service         # should list my_backend with description and doc link
uv run enveloper --service my_backend list
```

## Example Implementations

Refer to these files for complete examples of different store patterns:

| Store | File | Notes |
|-------|------|-------|
| AWS SSM | `src/enveloper/stores/aws_ssm.py` | Path-based keys, leading `/` prepended |
| GitHub Secrets | `src/enveloper/stores/github.py` | Write-only; uses simple key names |
| HashiCorp Vault | `src/enveloper/stores/vault.py` | KV v2 with mount/path, composite key stored |
| GCP Secret Mgr | `src/enveloper/stores/gcp_sm.py` | `--` separator, sanitized secret IDs |
| Azure Key Vault | `src/enveloper/stores/azure_kv.py` | `--` separator, sanitized secret names |
| Alibaba KMS | `src/enveloper/stores/aliyun_sm.py` | `--` separator, sanitized secret names |

## Testing Your Store

Create integration tests in `tests/integration/test_<store_name>.py`. Unit tests should use the autouse mock fixtures in `tests/conftest.py` which replace real keychain and cloud stores with in-memory fakes.

```python
import pytest
from enveloper.stores.my_backend import MyBackendStore


@pytest.mark.integration_my_backend
def test_roundtrip():
    store = MyBackendStore(prefix="test/")
    store.set("MY_KEY", "hello")
    assert store.get("MY_KEY") == "hello"
    store.delete("MY_KEY")
    assert store.get("MY_KEY") is None
```

Register the marker in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    # ... existing markers ...
    "integration_my_backend: integration tests for My Backend",
]
```

## Troubleshooting

**Store not appearing in `enveloper stores`:**
- Check that the entry point group is exactly `"enveloper.stores"` in `pyproject.toml`.
- Re-run `uv sync` after editing `pyproject.toml`.

**Import errors:**
- Ensure your class inherits from `SecretStore` and implements all four abstract methods.

**Key parsing issues:**
- `build_key` and `parse_key` rely on `key_separator`. If your backend prohibits `/` in names, override `key_separator` to something the backend allows (e.g., `"--"`).
- Use `sanitize_key_segment()` on domain/project/name values to strip the separator character.