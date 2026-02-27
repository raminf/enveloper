"""Shared fixtures for enveloper tests."""

from __future__ import annotations

from typing import Any

import pytest


class _FakeCloudStore:
    """In-memory store for unit tests so push/pull never touch real AWS or other clouds."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def list_keys(self) -> list[str]:
        return sorted(self._data.keys())

    def build_key(self, name: str, project: str, domain: str, version: str = "1.0.0") -> str:
        return f"envr/{domain}/{project}/{version}/{name}"


@pytest.fixture(autouse=True)
def _auto_mock_cloud_store(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure unit tests never push/pull to real AWS or other clouds; skip for integration tests."""
    integration_markers = [m.name for m in request.node.iter_markers() if m.name.startswith("integration_")]
    if integration_markers:
        return

    real_make_cloud_store = __import__("enveloper.resolve_store", fromlist=["make_cloud_store"]).make_cloud_store
    _REAL_CLOUD_STORES = ("aws", "github", "vault", "gcp", "azure", "aliyun")

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
        if store_name == "aws" and prefix == "":
            raise ValueError("prefix cannot be empty")
        if store_name == "aws" and region == "":
            raise ValueError("region cannot be empty")
        return _FakeCloudStore()

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
