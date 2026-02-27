"""Shared fixtures for enveloper tests."""

from __future__ import annotations

from typing import Any

import pytest

from enveloper.store import DEFAULT_PREFIX, DEFAULT_VERSION, SecretStore, is_valid_semver


class _FakeCloudStore(SecretStore):
    """In-memory store for unit tests so push/pull never touch real AWS or other clouds."""

    # Shared data across all instances for testing
    _shared_data: dict[str, dict[str, str]] = {}

    # Use base class default_namespace, key_separator, prefix (do not hardcode "envr" or "/")
    service_name: str = "fake"
    service_display_name: str = "Fake Cloud Store"
    service_doc_url: str = ""

    def __init__(self, store_id: str | None = None, version: str | None = None) -> None:
        self._store_id = store_id or "default"
        self._version = version or DEFAULT_VERSION
        if self._store_id not in _FakeCloudStore._shared_data:
            _FakeCloudStore._shared_data[self._store_id] = {}

    def get(self, key: str) -> str | None:
        return _FakeCloudStore._shared_data[self._store_id].get(key)

    def set(self, key: str, value: str) -> None:
        _FakeCloudStore._shared_data[self._store_id][key] = value

    def delete(self, key: str) -> None:
        _FakeCloudStore._shared_data[self._store_id].pop(key, None)

    def list_keys(self) -> list[str]:
        """Return keys in this store; when keys are composite (prefix/domain/project/version/name), filter by this store's version."""
        all_keys = sorted(_FakeCloudStore._shared_data[self._store_id].keys())
        # If keys look like composite keys (contain key_separator and parse), filter by version
        result: list[str] = []
        for key in all_keys:
            parsed = self.parse_key(key)
            if parsed and parsed.get("version") == self._version:
                result.append(key)
            elif not parsed:
                result.append(key)
        return result

    def build_key(self, name: str, project: str, domain: str, version: str = DEFAULT_VERSION) -> str:
        """Build a key using the store's separator and prefix."""
        # Sanitize all segments to prevent key_separator in names
        name_safe = self.sanitize_key_segment(name)
        project_safe = self.sanitize_key_segment(project)
        domain_safe = self.sanitize_key_segment(domain)

        sep = self.version_separator
        version_safe = version.replace(".", sep)
        prefix = self._get_prefix()
        return f"{prefix}{self.key_separator}{domain_safe}{self.key_separator}{project_safe}{self.key_separator}{version_safe}{self.key_separator}{name_safe}"

    def key_to_export_name(self, key: str) -> str:
        """Return the key name for export (strip prefix, domain, project, version)."""
        parsed = self.parse_key(key)
        if parsed:
            return parsed["name"]
        # Fallback: strip by separator
        if self.key_separator in key:
            return key.rsplit(self.key_separator, 1)[-1]
        return key

    def _get_prefix(self) -> str:
        """Get the prefix for this store instance."""
        return self.prefix

    def parse_key(self, key: str) -> dict[str, str] | None:
        """Parse a key and return its components."""
        sep = self.key_separator
        # Strip leading/trailing separator
        stripped = key.strip(sep) if sep else key
        if not stripped:
            return None
        parts = stripped.split(sep)
        if len(parts) < 5:
            return None

        # Order: prefix, domain, project, version, name (last five segments)
        try:
            name = parts[-1]
            version = parts[-2]
            project = parts[-4]
            domain = parts[-3]
            prefix = parts[-5]

            # Convert version separator back to dots
            version_normalized = version.replace("_", ".")

            return {
                "prefix": prefix,
                "project": project,
                "domain": domain,
                "version": version_normalized,
                "name": name,
            }
        except (IndexError, ValueError):
            return None

    @classmethod
    def clear_all(cls) -> None:
        """Clear all shared data."""
        cls._shared_data.clear()

    @classmethod
    def get_data(cls, store_id: str) -> dict[str, str]:
        """Get data for a specific store."""
        return cls._shared_data.get(store_id, {})


@pytest.fixture(autouse=True)
def _auto_mock_cloud_store(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure unit tests never push/pull to real AWS or other clouds; skip for integration tests."""
    integration_markers = [m.name for m in request.node.iter_markers() if m.name.startswith("integration_")]
    if integration_markers:
        return

    real_make_cloud_store = __import__("enveloper.resolve_store", fromlist=["make_cloud_store"]).make_cloud_store
    _REAL_CLOUD_STORES = ("aws", "github", "vault", "gcp", "azure", "aliyun")

    # Track store instances by their unique identifier
    _store_instances: dict[str, _FakeCloudStore] = {}

    def fake_make_cloud_store(
        store_name: str,
        cfg: Any,
        domain: str,
        env_name: str | None,
        *,
        project: str | None = None,
        prefix: str | None = None,
        profile: str | None = None,
        region: str | None = None,
        repo: str | None = None,
        version: str | None = None,
    ) -> _FakeCloudStore:
        if store_name not in _REAL_CLOUD_STORES:
            return real_make_cloud_store(
                store_name, cfg, domain, env_name,
                project=project, prefix=prefix, profile=profile, region=region,
                repo=repo, version=version,
            )
        version_str = version or DEFAULT_VERSION
        if not is_valid_semver(version_str):
            raise ValueError(f"Invalid version format: {version_str}. Must be valid semver (e.g., 1.0.0)")
        if store_name == "aws" and prefix == "":
            raise ValueError("prefix cannot be empty")
        if store_name == "aws" and region == "":
            raise ValueError("region cannot be empty")

        project_str = project or "_default_"
        domain_str = domain or "_default_"
        store_id = f"{store_name}:{domain_str}:{project_str}"

        if store_id not in _store_instances:
            _store_instances[store_id] = _FakeCloudStore(store_id, version=version_str)
        else:
            _store_instances[store_id]._version = version_str

        return _store_instances[store_id]

    monkeypatch.setattr("enveloper.resolve_store.make_cloud_store", fake_make_cloud_store)
    # CLI imports make_cloud_store at module level as resolve_make_cloud_store;
    # patch that reference too so push/pull in CLI tests use the fake store.
    monkeypatch.setattr("enveloper.cli.resolve_make_cloud_store", fake_make_cloud_store)


@pytest.fixture(autouse=True)
def _auto_mock_keyring(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure unit tests never touch the real keychain; skip for integration tests.

    Without this, any test that invokes the CLI with default/local service and
    project/domain (e.g. project=test, domain=aws) would write to the real OS
    keychain and leave entries like envr:test, aws/__keys__, aws/1.0.0/FOO.
    Integration tests (marked integration_*) are not mocked and use real backends.
    """
    integration_markers = [m.name for m in request.node.iter_markers() if m.name.startswith("integration_")]
    if integration_markers:
        return
    store: dict[tuple[str, str], str] = {}

    def _get(service: str, username: str) -> str | None:
        return store.get((service, username))

    def _set(service: str, username: str, password: str) -> None:
        store[(service, username)] = password

    def _delete(service: str, username: str) -> None:
        key = (service, username)
        if key not in store:
            import keyring.errors
            raise keyring.errors.PasswordDeleteError(username)
        del store[key]

    monkeypatch.setattr("keyring.get_password", _get)
    monkeypatch.setattr("keyring.set_password", _set)
    monkeypatch.setattr("keyring.delete_password", _delete)


@pytest.fixture()
def mock_keyring(monkeypatch: pytest.MonkeyPatch) -> dict[tuple[str, str], str]:
    """Replace the real keyring backend with an in-memory dict.

    Returns the backing dict so tests can inspect it directly.
    """
    store: dict[tuple[str, str], str] = {}

    def _get(service: str, username: str) -> str | None:
        return store.get((service, username))

    def _set(service: str, username: str, password: str) -> None:
        store[(service, username)] = password

    def _delete(service: str, username: str) -> None:
        key = (service, username)
        if key not in store:
            import keyring.errors

            raise keyring.errors.PasswordDeleteError(username)
        del store[key]

    monkeypatch.setattr("keyring.get_password", _get)
    monkeypatch.setattr("keyring.set_password", _set)
    monkeypatch.setattr("keyring.delete_password", _delete)

    return store


@pytest.fixture()
def sample_env(tmp_path):
    """Create a sample .env file and return its path."""
    content = """\
TWILIO_API_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN="my secret token"
export MESSAGING_PROVIDER=twilio

# Quoted values
SINGLE_QUOTED='hello world'
INLINE_COMMENT=some_value # this is a comment
EMPTY_VALUE=
EQUALS_IN_VALUE=postgres://user:pass@host/db?opt=1
"""
    p = tmp_path / ".env"
    p.write_text(content)
    return p
